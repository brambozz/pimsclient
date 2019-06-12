from unittest.mock import Mock

import pytest

from pimsclient.client import Project, KeyTypeFactory, TypedKeyFactoryException, NoConnectionException, \
    PIMSConnection, TypedPseudonym
from pimsclient.swagger import Key
from tests.factories import IdentifierFactory, PseudonymFactory, TypedKeyFactory, RequestsMockResponseExamples, \
    KeyFileFactory, TypedPseudonymFactory, TypedIdentifierFactory


@pytest.fixture()
def mock_project():
    """A project with a mock connection that does not hit any server
    Instead calls to pseudonymize and reidentify will return a random list Key objects with valid value_types
    """

    mock_connection = Mock(spec=PIMSConnection)
    mock_connection.pseudonymize.return_value = [TypedKeyFactory() for _ in range(20)]
    mock_connection.reidentify.return_value = [TypedKeyFactory() for _ in range(20)]
    return Project(key_file_id=1, connection=mock_connection)


def test_project_no_connection():
    """Creating a project without a connection is possible, but calling server-hitting methods will fail"""
    project = Project(key_file_id=1, connection=None)
    with pytest.raises(NoConnectionException):
        project.reidentify(pseudonyms=[])

    with pytest.raises(NoConnectionException):
        project.pseudonymize(identifiers=[])


def test_project_functions(mock_project):
    keys = mock_project.pseudonymize(identifiers=[])
    assert len(keys) == 20

    keys = mock_project.reidentify(pseudonyms=[])
    assert len(keys) == 20


def test_typed_key_factory_exception():
    """Trying to create a typed key for an unknown type should fail"""
    key = Key(identifier=IdentifierFactory(source='UNKNOWN'), pseudonym=PseudonymFactory())

    with pytest.raises(TypedKeyFactoryException):
        KeyTypeFactory().create_typed_key(key)

    with pytest.raises(TypedKeyFactoryException):
        KeyTypeFactory().create_typed_pseudonym(PseudonymFactory(), value_type='UNKNOWN')


@pytest.mark.parametrize('value_type', ['PatientID',
                                        'StudyInstanceUID',
                                        'SeriesInstanceUID',
                                        'SOPInstanceUID'])
def test_typed_key_factory(value_type):
    """Creating typed keys for these value types should work"""
    key = Key(identifier=IdentifierFactory(source=value_type), pseudonym=PseudonymFactory())

    typed_key = KeyTypeFactory().create_typed_key(key)
    assert typed_key.value_type == value_type


def test_pimsconnection(mock_pims_session):
    connection = PIMSConnection(session=mock_pims_session)
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.KEYFILES_PSEUDONYMS_REIDENTIFY_RESPONSE
    )
    connection.pseudonymize(key_file=KeyFileFactory(), identifiers=[IdentifierFactory()])
    connection.reidentify(key_file=KeyFileFactory(), pseudonyms=[PseudonymFactory()])


def test_str():
    project = Project(key_file_id=0, connection=Mock())
    string = f'{IdentifierFactory()}{project}{project.get_name()}{TypedKeyFactory()}{TypedIdentifierFactory}' \
        f'{TypedPseudonym(value="kees")}'

    assert string

