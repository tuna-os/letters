"""
Tests for .github/scripts/update-index.py

Covers parsing of OCI layouts, Flatpak label validation, index file
creation and update, and all main error paths — without requiring
a container runtime or network access.
"""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Load update-index.py via importlib (hyphen in filename prevents normal import)
_SCRIPT_PATH = Path(__file__).resolve().parent.parent / ".github" / "scripts" / "update-index.py"
_spec = importlib.util.spec_from_file_location("update_index", _SCRIPT_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
main = _mod.main


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_oci(tmp_dir: Path, manifest_digest: str, config_digest: str,
              config: dict) -> Path:
    """Create a minimal OCI layout directory under *tmp_dir* and return it.

    Parameters
    ----------
    tmp_dir : Path
        Base temporary directory (caller manages lifecycle).
    manifest_digest : str
        Hex hash for the manifest blob (no 'sha256:' prefix).
    config_digest : str
        Hex hash for the config blob.
    config : dict
        OCI image config JSON (architecture, os, config.Labels, etc.).
    """
    oci_dir = tmp_dir / "oci-layout"
    blobs_dir = oci_dir / "blobs" / "sha256"
    blobs_dir.mkdir(parents=True)

    # index.json — references the manifest
    index = {
        "schemaVersion": 2,
        "manifests": [
            {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "digest": f"sha256:{manifest_digest}",
                "size": 1234,
            }
        ],
    }
    (oci_dir / "index.json").write_text(json.dumps(index))

    # manifest.json — references the config
    manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "mediaType": "application/vnd.oci.image.config.v1+json",
            "digest": f"sha256:{config_digest}",
            "size": 567,
        },
        "layers": [],
    }
    (blobs_dir / manifest_digest).write_text(json.dumps(manifest))

    # config.json — carries architecture, os, and flatpak labels
    (blobs_dir / config_digest).write_text(json.dumps(config))

    return oci_dir


def _run_main(oci_dir: Path, index_file: Path, repo_name: str = "test/repo",
              tags: list[str] | None = None, registry: str = "ghcr.io"):
    """Invoke *main* with the given arguments via sys.argv patching."""
    argv = [
        "update-index.py",
        "--oci-dir", str(oci_dir),
        "--index-file", str(index_file),
        "--repo-name", repo_name,
        "--registry", registry,
    ]
    if tags:
        argv += ["--tags"] + tags
    with patch.object(sys, "argv", argv):
        main()


# ── fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def flatpak_config():
    """Minimal OCI config with valid Flatpak labels."""
    return {
        "architecture": "amd64",
        "os": "linux",
        "config": {
            "Labels": {
                "org.flatpak.ref": "app/org.test.App/x86_64/stable",
                "org.flatpak.metadata": "Metadata for testing",
                "org.flatpak.name": "Test App",
                "org.flatpak.title": "Test Flatpak Application",
            },
        },
        "rootfs": {"type": "layers", "diff_ids": []},
    }


@pytest.fixture
def manifest_hash():
    return "a" * 64


@pytest.fixture
def config_hash():
    return "b" * 64


# ── Happy-path tests ──────────────────────────────────────────────────────────

class TestUpdateIndexHappyPath:
    """Core functionality: parsing and index file creation."""

    def test_creates_new_index_file(self, tmp_path, manifest_hash,
                                    config_hash, flatpak_config):
        """Should create a new index/static file when none exists."""
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash,
                            flatpak_config)
        idx_file = tmp_path / "index" / "static"

        _run_main(oci_dir, idx_file)

        assert idx_file.exists()
        data = json.loads(idx_file.read_text())
        assert data["Registry"] == "https://ghcr.io"
        assert len(data["Results"]) == 1
        assert data["Results"][0]["Name"] == "test/repo"

    def test_populates_correct_image_entry(self, tmp_path, manifest_hash,
                                           config_hash, flatpak_config):
        """Image entry should have correct Digest, OS, Arch, Tags, Labels."""
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash,
                            flatpak_config)
        idx_file = tmp_path / "index" / "static"

        _run_main(oci_dir, idx_file, tags=["latest", "v1.0"])

        data = json.loads(idx_file.read_text())
        images = data["Results"][0]["Images"]
        assert len(images) == 1
        img = images[0]

        assert img["Digest"] == f"sha256:{manifest_hash}"
        assert img["MediaType"] == "application/vnd.oci.image.manifest.v1+json"
        assert img["OS"] == "linux"
        assert img["Architecture"] == "amd64"
        assert img["Tags"] == ["latest", "v1.0"]

        # Only org.flatpak.* labels should be included
        assert "org.flatpak.ref" in img["Labels"]
        assert "org.flatpak.metadata" in img["Labels"]
        assert "org.flatpak.name" in img["Labels"]
        assert "org.flatpak.title" in img["Labels"]

    def test_appends_new_repo_to_existing_index(self, tmp_path, manifest_hash,
                                                 config_hash, flatpak_config):
        """Should add a new Results entry when the repo doesn't exist yet."""
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash,
                            flatpak_config)
        idx_file = tmp_path / "index" / "static"

        # Pre-populate index with a different repo
        idx_file.parent.mkdir(parents=True)
        idx_file.write_text(json.dumps({
            "Registry": "https://ghcr.io",
            "Results": [
                {
                    "Name": "other/repo",
                    "Images": [{"Architecture": "amd64", "Digest": "old"}],
                },
            ],
        }))

        _run_main(oci_dir, idx_file, repo_name="test/repo")

        data = json.loads(idx_file.read_text())
        names = [r["Name"] for r in data["Results"]]
        assert names == ["other/repo", "test/repo"]

    def test_replaces_existing_architecture(self, tmp_path, manifest_hash,
                                             config_hash, flatpak_config):
        """When the repo already exists, replace the entry for same arch."""
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash,
                            flatpak_config)
        idx_file = tmp_path / "index" / "static"

        # Pre-populate index with the same repo and arch
        idx_file.parent.mkdir(parents=True)
        idx_file.write_text(json.dumps({
            "Registry": "https://ghcr.io",
            "Results": [
                {
                    "Name": "test/repo",
                    "Images": [
                        {"Architecture": "amd64", "Digest": "old-digest"},
                    ],
                },
            ],
        }))

        _run_main(oci_dir, idx_file, repo_name="test/repo")

        data = json.loads(idx_file.read_text())
        images = data["Results"][0]["Images"]
        assert len(images) == 1  # replaced, not appended
        assert images[0]["Digest"] == f"sha256:{manifest_hash}"

    def test_preserves_other_architectures(self, tmp_path, manifest_hash,
                                            config_hash, flatpak_config):
        """Replacing an arch should not affect other arch entries."""
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash,
                            flatpak_config)
        idx_file = tmp_path / "index" / "static"

        # Pre-populate with an arm64 entry
        idx_file.parent.mkdir(parents=True)
        idx_file.write_text(json.dumps({
            "Registry": "https://ghcr.io",
            "Results": [
                {
                    "Name": "test/repo",
                    "Images": [
                        {"Architecture": "arm64", "Digest": "keep-me"},
                    ],
                },
            ],
        }))

        _run_main(oci_dir, idx_file, repo_name="test/repo")

        data = json.loads(idx_file.read_text())
        images = data["Results"][0]["Images"]
        arches = {img["Architecture"] for img in images}
        assert arches == {"amd64", "arm64"}
        # arm64 entry is untouched
        arm_img = next(img for img in images if img["Architecture"] == "arm64")
        assert arm_img["Digest"] == "keep-me"

    def test_custom_registry(self, tmp_path, manifest_hash,
                              config_hash, flatpak_config):
        """Should use the provided registry in the output URL."""
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash,
                            flatpak_config)
        idx_file = tmp_path / "index" / "static"

        _run_main(oci_dir, idx_file, registry="registry.example.com")

        data = json.loads(idx_file.read_text())
        assert data["Registry"] == "https://registry.example.com"

    def test_custom_tags(self, tmp_path, manifest_hash,
                          config_hash, flatpak_config):
        """Should store custom tags in the image entry."""
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash,
                            flatpak_config)
        idx_file = tmp_path / "index" / "static"

        _run_main(oci_dir, idx_file, tags=["stable", "v2.0.1"])

        data = json.loads(idx_file.read_text())
        assert data["Results"][0]["Images"][0]["Tags"] == ["stable", "v2.0.1"]

    def test_default_tags(self, tmp_path, manifest_hash,
                           config_hash, flatpak_config):
        """Should default to ['latest'] when no tags provided."""
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash,
                            flatpak_config)
        idx_file = tmp_path / "index" / "static"

        _run_main(oci_dir, idx_file)

        data = json.loads(idx_file.read_text())
        assert data["Results"][0]["Images"][0]["Tags"] == ["latest"]


# ── Edge cases / config variants ──────────────────────────────────────────────

class TestConfigVariants:
    """Different OCI config shapes."""

    def test_default_architecture(self, tmp_path, manifest_hash, config_hash):
        """When architecture is missing, default to amd64."""
        config = {
            "os": "linux",
            "config": {
                "Labels": {
                    "org.flatpak.ref": "app/org.test.App/x86_64/stable",
                    "org.flatpak.metadata": "test",
                },
            },
        }
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash, config)
        idx_file = tmp_path / "index" / "static"
        _run_main(oci_dir, idx_file)
        data = json.loads(idx_file.read_text())
        assert data["Results"][0]["Images"][0]["Architecture"] == "amd64"

    def test_default_os(self, tmp_path, manifest_hash, config_hash):
        """When os is missing, default to linux."""
        config = {
            "architecture": "arm64",
            "config": {
                "Labels": {
                    "org.flatpak.ref": "app/org.test.App/aarch64/stable",
                    "org.flatpak.metadata": "test",
                },
            },
        }
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash, config)
        idx_file = tmp_path / "index" / "static"
        _run_main(oci_dir, idx_file)
        data = json.loads(idx_file.read_text())
        assert data["Results"][0]["Images"][0]["OS"] == "linux"

    def test_no_config_labels(self, tmp_path, manifest_hash, config_hash):
        """Config with no Labels key at all -> raise ValueError."""
        config = {"architecture": "amd64", "os": "linux", "config": {}}
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash, config)
        idx_file = tmp_path / "index" / "static"
        with pytest.raises(ValueError, match="Missing required label"):
            _run_main(oci_dir, idx_file)

    def test_extra_non_flatpak_labels_excluded(self, tmp_path, manifest_hash,
                                                config_hash):
        """Non-org.flatpak labels should not appear in the image entry."""
        config = {
            "architecture": "amd64",
            "os": "linux",
            "config": {
                "Labels": {
                    "org.flatpak.ref": "app/org.test.App/x86_64/stable",
                    "org.flatpak.metadata": "test",
                    "com.example.custom": "should-not-appear",
                    "org.freedesktop": "also-excluded",
                },
            },
        }
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash, config)
        idx_file = tmp_path / "index" / "static"
        _run_main(oci_dir, idx_file)
        data = json.loads(idx_file.read_text())
        labels = data["Results"][0]["Images"][0]["Labels"]
        assert "com.example.custom" not in labels
        assert "org.freedesktop" not in labels
        assert "org.flatpak.ref" in labels

    def test_arm64_architecture(self, tmp_path, manifest_hash, config_hash):
        """Should handle non-amd64 architectures correctly."""
        config = {
            "architecture": "arm64",
            "os": "linux",
            "config": {
                "Labels": {
                    "org.flatpak.ref": "app/org.test.App/aarch64/stable",
                    "org.flatpak.metadata": "test",
                },
            },
        }
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash, config)
        idx_file = tmp_path / "index" / "static"
        _run_main(oci_dir, idx_file)
        data = json.loads(idx_file.read_text())
        assert data["Results"][0]["Images"][0]["Architecture"] == "arm64"


# ── Error-path tests ──────────────────────────────────────────────────────────

class TestErrorPaths:
    """Input validation and error handling."""

    def test_missing_index_json(self, tmp_path):
        """Should raise FileNotFoundError when index.json is missing."""
        oci_dir = tmp_path / "oci-layout"
        oci_dir.mkdir()
        idx_file = tmp_path / "output.json"
        with pytest.raises(FileNotFoundError, match="index.json not found"):
            _run_main(oci_dir, idx_file)

    def test_empty_manifests(self, tmp_path, manifest_hash, config_hash,
                              flatpak_config):
        """Should raise ValueError when manifests list is empty."""
        oci_dir = tmp_path / "oci-layout"
        blobs_dir = oci_dir / "blobs" / "sha256"
        blobs_dir.mkdir(parents=True)
        (oci_dir / "index.json").write_text(json.dumps({
            "schemaVersion": 2,
            "manifests": [],
        }))
        (blobs_dir / manifest_hash).write_text(
            json.dumps({"config": {"digest": f"sha256:{config_hash}"}})
        )
        (blobs_dir / config_hash).write_text(json.dumps(flatpak_config))
        idx_file = tmp_path / "output.json"
        with pytest.raises(ValueError, match="No manifests found"):
            _run_main(oci_dir, idx_file)

    def test_missing_manifest_blob(self, tmp_path, config_hash,
                                    flatpak_config):
        """Should raise FileNotFoundError when manifest blob is missing."""
        oci_dir = tmp_path / "oci-layout"
        blobs_dir = oci_dir / "blobs" / "sha256"
        blobs_dir.mkdir(parents=True)
        (oci_dir / "index.json").write_text(json.dumps({
            "schemaVersion": 2,
            "manifests": [
                {
                    "mediaType": "application/vnd.oci.image.manifest.v1+json",
                    "digest": "sha256:deadbeef" * 8,
                    "size": 1234,
                },
            ],
        }))
        # Don't create the manifest blob
        (blobs_dir / config_hash).write_text(json.dumps(flatpak_config))
        idx_file = tmp_path / "output.json"
        with pytest.raises(FileNotFoundError):
            _run_main(oci_dir, idx_file)

    def test_missing_flatpak_ref_label(self, tmp_path, manifest_hash,
                                        config_hash):
        """Should raise ValueError when org.flatpak.ref is missing."""
        config = {
            "architecture": "amd64",
            "os": "linux",
            "config": {
                "Labels": {
                    "org.flatpak.metadata": "test",
                },
            },
        }
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash, config)
        idx_file = tmp_path / "index" / "static"
        with pytest.raises(ValueError, match="Missing required label"):
            _run_main(oci_dir, idx_file)

    def test_missing_flatpak_metadata_label(self, tmp_path, manifest_hash,
                                              config_hash):
        """Should raise ValueError when org.flatpak.metadata is missing."""
        config = {
            "architecture": "amd64",
            "os": "linux",
            "config": {
                "Labels": {
                    "org.flatpak.ref": "app/org.test.App/x86_64/stable",
                },
            },
        }
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash, config)
        idx_file = tmp_path / "index" / "static"
        with pytest.raises(ValueError, match="Missing required label"):
            _run_main(oci_dir, idx_file)

    def test_missing_config_blob(self, tmp_path, manifest_hash):
        """Should raise FileNotFoundError when config blob is missing."""
        oci_dir = tmp_path / "oci-layout"
        blobs_dir = oci_dir / "blobs" / "sha256"
        blobs_dir.mkdir(parents=True)
        (oci_dir / "index.json").write_text(json.dumps({
            "schemaVersion": 2,
            "manifests": [
                {
                    "mediaType": "application/vnd.oci.image.manifest.v1+json",
                    "digest": f"sha256:{manifest_hash}",
                    "size": 1234,
                },
            ],
        }))
        # Create manifest but omit config blob
        (blobs_dir / manifest_hash).write_text(json.dumps({
            "config": {"digest": "sha256:cccc" + "0" * 60},
        }))
        idx_file = tmp_path / "output.json"
        with pytest.raises(FileNotFoundError):
            _run_main(oci_dir, idx_file)


# ── Idempotency ───────────────────────────────────────────────────────────────

class TestIdempotency:
    """Running the same input twice should produce the same output."""

    def test_repeated_run_is_idempotent(self, tmp_path, manifest_hash,
                                         config_hash, flatpak_config):
        """Running twice with the same inputs should yield identical output."""
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash,
                            flatpak_config)
        idx_file = tmp_path / "index" / "static"

        _run_main(oci_dir, idx_file, repo_name="test/repo",
                  tags=["latest"])
        expected = json.loads(idx_file.read_text())

        # Run again
        _run_main(oci_dir, idx_file, repo_name="test/repo",
                  tags=["latest"])
        actual = json.loads(idx_file.read_text())

        assert actual == expected

    def test_multiple_tags_idempotent(self, tmp_path, manifest_hash,
                                       config_hash, flatpak_config):
        """Re-running with same tags should not add duplicate entries."""
        oci_dir = _make_oci(tmp_path, manifest_hash, config_hash,
                            flatpak_config)
        idx_file = tmp_path / "index" / "static"

        for _ in range(3):
            _run_main(oci_dir, idx_file, repo_name="test/repo",
                      tags=["latest", "stable"])

        data = json.loads(idx_file.read_text())
        assert len(data["Results"][0]["Images"]) == 1
