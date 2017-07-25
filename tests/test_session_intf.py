from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pytest  # type: ignore

import nixnet
from nixnet import constants
from nixnet import errors


@pytest.fixture
def nixnet_in_interface(request):
    interface = request.config.getoption("--nixnet-in-interface")
    return interface


@pytest.fixture
def nixnet_out_interface(request):
    interface = request.config.getoption("--nixnet-out-interface")
    return interface


@pytest.mark.integration
def test_intf_container(nixnet_in_interface):
    database_name = 'NIXNET_example'
    cluster_name = 'CAN_Cluster'
    frame_name = 'CANEventFrame1'

    with nixnet.FrameInQueuedSession(
            nixnet_in_interface,
            database_name,
            cluster_name,
            frame_name) as input_session:
        assert str(input_session.intf) == nixnet_in_interface
        assert input_session.intf == nixnet_in_interface
        assert input_session.intf != "<random>"


@pytest.mark.integration
def test_intf_properties_settable_only_when_stopped(nixnet_out_interface):
    """Verify Interface properties settable only when stopped.

    Ensure that Interface properties are only allowed to be set when the session is stopped.
    """
    database_name = 'NIXNET_example'
    cluster_name = 'CAN_Cluster'
    frame_name = 'CANEventFrame1'

    with nixnet.FrameOutQueuedSession(
            nixnet_out_interface,
            database_name,
            cluster_name,
            frame_name) as output_session:
        # Start the session manually
        output_session.start()

        # These should error because interfrace properties can only be modified
        # when the session is stopped. Note that we've only picked a select few
        # interface properties to test this behavior.
        with pytest.raises(errors.XnetError) as term_excinfo:
            output_session.intf.can_term = constants.CanTerm.ON
        assert term_excinfo.value.error_type == constants.Err.OBJECT_STARTED

        with pytest.raises(errors.XnetError) as baud_rate_excinfo:
            output_session.intf.baud_rate = 100000
        assert baud_rate_excinfo.value.error_type == constants.Err.OBJECT_STARTED

        with pytest.raises(errors.XnetError) as transmit_pause_excinfo:
            output_session.intf.can_transmit_pause = True
        assert transmit_pause_excinfo.value.error_type == constants.Err.OBJECT_STARTED

        output_session.stop()

        # Should not error because the session has stopped.
        output_session.intf.can_term = constants.CanTerm.ON
        output_session.intf.baud_rate = 100000
        output_session.intf.can_transmit_pause = True

        assert output_session.intf.can_term == constants.CanTerm.ON
        assert output_session.intf.baud_rate == 100000
        assert output_session.intf.can_transmit_pause


@pytest.mark.integration
def test_stream_session_requires_baud_rate(nixnet_out_interface):
    """Stream session requires setting baud rate.

    Ensure Stream session cannot start without setting the baud_rate property.
    """
    with nixnet.FrameOutStreamSession(nixnet_out_interface) as output_session:
        with pytest.raises(errors.XnetError) as start_excinfo:
            output_session.start()
        assert start_excinfo.value.error_type == constants.Err.BAUD_RATE_NOT_CONFIGURED

        output_session.intf.baud_rate = 125000
        assert output_session.intf.baud_rate == 125000

        # Starting the stream session does not error because the baud_rate is set
        output_session.start()