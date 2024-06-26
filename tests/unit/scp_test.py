# -*- coding: utf-8 -*-

"""Tests suite for scp."""

import os
import random
import string
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


@pytest.fixture
def pre_existing_file_path(tmp_path):
    """Return local path for a pre-populated file."""
    path = tmp_path / 'pre-existing-file.txt'
    path.write_bytes(b'whatever')
    return path


def test_get_existing_local(pre_existing_file_path, src_path, ssh_scp, transmit_payload):
    """Check that SCP file download works and overwrites local file if it exists."""
    ssh_scp.get(str(src_path), str(pre_existing_file_path))
    assert pre_existing_file_path.read_bytes() == transmit_payload


@pytest.fixture
def large_payload():
    """Generate a large 65537 byte (64kB+1B) test payload."""
    random_char_kilobyte = [ord(random.choice(string.printable)) for _ in range(1024)]
    full_bytes_number = 64
    a_64kB_chunk = bytes(random_char_kilobyte * full_bytes_number)
    the_last_byte = random.choice(random_char_kilobyte).to_bytes(length=1, byteorder='big')
    return a_64kB_chunk + the_last_byte


@pytest.fixture
def src_path_large(tmp_path, large_payload):
    """Return a remote path that to a 65537 byte-sized file.

    Typical single-read chunk size is 64kB in ``libssh`` so
    the test needs a file that would overflow that to trigger
    the read loop.
    """
    path = tmp_path / 'large.txt'
    path.write_bytes(large_payload)
    return path


def test_get_large(dst_path, src_path_large, ssh_scp, large_payload):
    """Check that SCP file download gets over 64kB of data."""
    ssh_scp.get(str(src_path_large), str(dst_path))
    assert dst_path.read_bytes() == large_payload
