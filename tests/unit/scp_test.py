# -*- coding: utf-8 -*-

"""Tests suite for scp."""

import os
import uuid

import pytest

from pylibsshext.errors import LibsshSCPException


@pytest.fixture
def ssh_scp(ssh_client_session):
    """Initialize an SCP session and destroy it after testing."""
    scp = ssh_client_session.scp()
    try:  # noqa: WPS501
        yield scp
    finally:
        del scp  # noqa: WPS420


@pytest.fixture
def transmit_payload():
    """Generate a binary test payload."""
    uuid_name = uuid.uuid4()
    return 'Hello, {name!s}'.format(name=uuid_name).encode()


@pytest.fixture
def file_paths_pair(tmp_path, transmit_payload):
    """Populate a source file and make a destination path."""
    src_path = tmp_path / 'src-file.txt'
    dst_path = tmp_path / 'dst-file.txt'
    src_path.write_bytes(transmit_payload)
    return src_path, dst_path


@pytest.fixture
def src_path(file_paths_pair):
    """Return a data source path."""
    return file_paths_pair[0]


@pytest.fixture
def dst_path(file_paths_pair):
    """Return a data destination path."""
    path = file_paths_pair[1]
    assert not path.exists()
    return path


def test_put(dst_path, src_path, ssh_scp, transmit_payload):
    """Check that SCP file transfer works."""
    ssh_scp.put(str(src_path), str(dst_path))
    assert dst_path.read_bytes() == transmit_payload


def test_get(dst_path, src_path, ssh_scp, transmit_payload):
    """Check that SCP file download works."""
    ssh_scp.get(str(src_path), str(dst_path))
    assert dst_path.read_bytes() == transmit_payload


@pytest.fixture
def path_to_non_existent_src_file(tmp_path):
    """Return a remote path that does not exist."""
    path = tmp_path / 'non-existing.txt'
    assert not path.exists()
    return path


def test_copy_from_non_existent_remote_path(path_to_non_existent_src_file, ssh_scp):
    """Check that SCP file download raises exception if the remote file is missing."""
    error_msg = '^Error receiving information about file:'
    with pytest.raises(LibsshSCPException, match=error_msg):
        ssh_scp.get(str(path_to_non_existent_src_file), os.devnull)
