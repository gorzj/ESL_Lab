from pygmyhdl import *


@chunk
def counter(clk_i, cnt_o):
    # Here's the counter state variable.
    cnt = Bus(len(cnt_o))

    # The next state logic is just an adder that adds 1 to the current cnt state variable.
    @seq_logic(clk_i.posedge)
    def next_state_logic():
        cnt.next = cnt + 1

    # The output logic just sends the current cnt state variable to the output.
    @comb_logic
    def output_logic():
        cnt_o.next = cnt


initialize()
clk = Wire(name='clk')
cnt = Bus(3, name='cnt')
counter(clk_i=clk, cnt_o=cnt)
clk_sim(clk, num_cycles=10)
show_waveforms()


@chunk
def counter_en_rst(clk_i, en_i, rst_i, cnt_o):
    cnt = Bus(len(cnt_o))

    # The next state logic now includes a reset input to clear the counter
    # to zero, and an enable input that only allows counting when it is true.
    @seq_logic(clk_i.posedge)
    def next_state_logic():
        if rst == True:
            cnt.next = 0
        elif en == True:
            cnt.next = cnt + 1
        else:
            # No reset and no enable, so just keep the counter at its current value.
            pass

    @comb_logic
    def output_logic():
        cnt_o.next = cnt


initialize()
clk = Wire(name='clk')
rst = Wire(1, name='rst')
en = Wire(1, name='en')
cnt = Bus(3, name='cnt')
counter_en_rst(clk_i=clk, rst_i=rst, en_i=en, cnt_o=cnt)


def cntr_tb():
    '''Test bench for the counter with a reset and enable inputs.'''

    # Enable the counter for a few cycles.
    rst.next = 0
    en.next = 1
    for _ in range(4):
        clk.next = 0
        yield delay(1)
        clk.next = 1
        yield delay(1)

    # Disable the counter for a few cycles.
    en.next = 0
    for _ in range(2):
        clk.next = 0
        yield delay(1)
        clk.next = 1
        yield delay(1)

    # Re-enable the counter for a few cycles.
    en.next = 1
    for _ in range(2):
        clk.next = 0
        yield delay(1)
        clk.next = 1
        yield delay(1)

    # Reset the counter.
    rst.next = 1
    clk.next = 0
    yield delay(1)
    clk.next = 1
    yield delay(1)

    # Start counting again.
    rst.next = 0
    for _ in range(4):
        clk.next = 0
        yield delay(1)
        clk.next = 1
        yield delay(1)


simulate(cntr_tb())
show_waveforms(tick=True)


@chunk
def debouncer(clk_i, button_i, button_o, debounce_time):
    '''
    Inputs:
        clk_i: Main clock input.
        button_i: Raw button input.
        button_o: Debounced button output.
        debounce_time: Number of clock cycles the button value has to be stable.
    '''

    # These are the state variables of the FSM.
    from math import ceil, log2
    debounce_cnt = Bus(int(ceil(log2(debounce_time + 1))), name='dbcnt')  # Counter big enough to store debounce time.
    prev_button = Wire(name='prev_button')  # Stores the button value from the previous clock cycle.

    @seq_logic(clk_i.posedge)
    def next_state_logic():
        if button_i == prev_button:
            # If the current and previous button values are the same, decrement the counter
            # until it reaches zero and then stop.
            if debounce_cnt != 0:
                debounce_cnt.next = debounce_cnt - 1
        else:
            # If the current and previous button values aren't the same, then the button must
            # still be bouncing so reset the counter to the debounce interval and try again.
            debounce_cnt.next = debounce_time

        # Store the current button value for comparison during the next clock cycle.
        prev_button.next = button_i

    @seq_logic(clk_i.posedge)
    def output_logic():
        if debounce_cnt == 0:
            # Output the stable button value whenever the counter is zero.
            # Don't use the actual button input value because that could change at any time.
            button_o.next = prev_button


initialize()  # Initialize for simulation here because we'll be watching the internal debounce counter.

clk = Wire(name='clk')
button_i = Wire(name='button_i')
button_o = Wire(name='button_o')
debouncer(clk, button_i, button_o, 3)


def debounce_tb():
    '''Test bench for the counter with a reset and enable inputs.'''

    # Initialize the button and leave it stable for the debounce time.
    button_i.next = 1
    for _ in range(4):
        clk.next = 0
        yield delay(1)
        clk.next = 1
        yield delay(1)

    # Blip the button for less than the debounce time and show the debounced output does not change.
    button_i.next = 0
    for _ in range(2):
        clk.next = 0
        yield delay(1)
        clk.next = 1
        yield delay(1)
    button_i.next = 1
    for _ in range(2):
        clk.next = 0
        yield delay(1)
        clk.next = 1
        yield delay(1)

    # Press the button for more than the debounce time and show the debounced output changes.
    button_i.next = 0
    for _ in range(5):
        clk.next = 0
        yield delay(1)
        clk.next = 1
        yield delay(1)


simulate(debounce_tb())
show_waveforms(tick=True)


@chunk
def classic_fsm(clk_i, inputs_i, outputs_o):
    fsm_state = State('A', 'B', 'C', 'D', name='state')
    reset_cnt = Bus(2)

    prev_inputs = Bus(len(inputs_i), name='prev_inputs')
    input_chgs = Bus(len(inputs_i), name='input_chgs')

    # Take the inputs and run them through the debounce circuits.
    dbnc_inputs = Bus(len(inputs_i))  # These are the inputs after debouncing.
    debounce_time = 120000
    debouncer(clk_i, inputs_i.o[0], dbnc_inputs.i[0], debounce_time)
    debouncer(clk_i, inputs_i.o[1], dbnc_inputs.i[1], debounce_time)

    # The edge detection of the inputs is now performed on the debounced inputs.
    @comb_logic
    def detect_chg():
        input_chgs.next = dbnc_inputs & ~prev_inputs

    @seq_logic(clk_i.posedge)
    def next_state_logic():
        if reset_cnt < reset_cnt.max - 1:
            fsm_state.next = fsm_state.s.A
            reset_cnt.next = reset_cnt + 1
        elif fsm_state == fsm_state.s.A:
            if input_chgs[0]:
                fsm_state.next = fsm_state.s.B
            elif input_chgs[1]:
                fsm_state.next = fsm_state.s.D
        elif fsm_state == fsm_state.s.B:
            if input_chgs[0]:
                fsm_state.next = fsm_state.s.C
            elif input_chgs[1]:
                fsm_state.next = fsm_state.s.A
        elif fsm_state == fsm_state.s.C:
            if input_chgs[0]:
                fsm_state.next = fsm_state.s.D
            elif input_chgs[1]:
                fsm_state.next = fsm_state.s.B
        elif fsm_state == fsm_state.s.D:
            if input_chgs[0]:
                fsm_state.next = fsm_state.s.A
            elif input_chgs[1]:
                fsm_state.next = fsm_state.s.C
        else:
            fsm_state.next = fsm_state.s.A

        prev_inputs.next = dbnc_inputs  # Store the debounced inputs.

    @comb_logic
    def output_logic():
        if fsm_state == fsm_state.s.A:
            outputs_o.next = 0b0001
        elif fsm_state == fsm_state.s.B:
            outputs_o.next = 0b0010
        elif fsm_state == fsm_state.s.C:
            outputs_o.next = 0b0100
        elif fsm_state == fsm_state.s.D:
            outputs_o.next = 0b1000
        else:
            outputs_o.next = 0b1111


initialize()

inputs = Bus(2, name='inputs')
outputs = Bus(4, name='outputs')
clk = Wire(name='clk')
classic_fsm(clk, inputs, outputs)


def fsm_tb():
    nop = 0b00
    fwd = 0b01
    bck = 0b10

    ins = [nop, nop, nop, nop, fwd, fwd, fwd, bck, bck, bck]
    for inputs.next in ins:
        clk.next = 0
        yield delay(1)
        clk.next = 1
        yield delay(1)

    # Interspersed active and inactive inputs.
    ins = [fwd, nop, fwd, nop, fwd, nop, bck, nop, bck, nop, bck, nop]
    for inputs.next in ins:
        clk.next = 0
        yield delay(1)
        clk.next = 1
        yield delay(1)


simulate(fsm_tb())
show_waveforms('clk inputs prev_inputs input_chgs state outputs', tick=True, width=2000)

toVerilog(classic_fsm, clk_i=Wire(), inputs_i=Bus(2), outputs_o=Bus(4))

with open('classic_fsm.pcf', 'w') as pcf:
    pcf.write(
'''
set_io clk_i 21
set_io outputs_o[0] 99
set_io outputs_o[1] 98
set_io outputs_o[2] 97
set_io outputs_o[3] 96
set_io inputs_i[0] 118
set_io inputs_i[1] 114
'''
    )



