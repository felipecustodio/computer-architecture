import logging
logging.basicConfig(filename='results.log',filemode='w',format='%(message)s',level=logging.DEBUG)

class Unit:
    """ Describes a functional unit """
    def __init__(self, name):
        """ Constructor """
        self.name = name
        self.busy = False
        self.op = None
        self.fi = 0
        self.fj = 0
        self.fk = 0
        self.qj = None
        self.qk = None
        self.rj = False
        self.rk = False

    def print(self):
        """ Display status """
        logging.debug(self.name+"\t"+str(self.busy)+"\t"+str(self.op)+"\t"+str(self.fi)+"\t"+str(self.fj)+"\t"+str(self.fk)+"\t"+str(self.qj)+"\t"+str(self.qk)+"\t"+str(self.rj)+"\t"+str(self.rk))

    def to_html(self):
        """ Display status for HTML parses """
        return [self.name,str(self.busy),str(self.op),str(self.fi),str(self.fj),str(self.fk),str(self.qj),str(self.qk),str(self.rj),str(self.rk)]


class Instruction:
    """ Describes an instruction and its stages """
    def __init__(self, index, op, dst, src1, src2):
        """ Constructor """
        self.index = index
        # operands
        self.op = op
        self.dst = dst
        self.src1 = src1
        self.src2 = src2
        # clock cycles / stages
        # issue, read_op, exec_begin, exec_end, write_back
        self.stages = {"issue":0,"read_op":0,"exec_begin":0,"exec_end":0,"write_back":0, "finished":0}
        self.current_stage = "issue"

    def print(self):
        """ Display status """
        logging.debug(self.op + " " + str(self.dst) + " " + str(self.src1) + " " + str(self.src2) + "\t" + str(self.stages))

    def to_html(self):
        """ Display for HTML parser """
        return (self.op + " " + str(self.dst) + " " + str(self.src1) + " " + str(self.src2))

# clock
clock = 1

# code
instruction_index = 0 # current instruction
instructions = [] # stores all parsed instructions
finished_counter = 0

# operations
memory_operations = ['lw', 'sw']
arithmetic_operations = ['add', 'addi', 'mult', 'div']

# execution delays
delay_ldu = 1 # how long does a memory operation take
delay_alu = 0 # how long does a arithmetic operation take

# result registers
result = dict.fromkeys(['$2','$3','$4','$5', None], False) # results registers

# functional units
ld_units = []
al_units = []

# html to display results
html = ""
header_units = ['name','busy', 'op', 'fi', 'fj', 'fk', 'fj', 'fk', 'qj', 'qk', 'rj', 'rk']
header_inst = ['inst', 'issue', 'read_op', 'exec_begin', 'exec_end', 'write_back']
header_regs = ['register', 'status']


def init_ldu(number):
    global ld_units
    for i in range(number):
        name = "LDU" + str(i)
        ld_units.append([Unit(name), None])


def init_alu(number):
    global al_units
    for i in range(number):
        name = "ALU" + str(i)
        al_units.append([Unit(name), None])


def status():
    """ Logs the current status of everything """
    global html
    global instructions


    instructions_table = []

    regs_table = []

    units_table = []

    logging.debug("\nINSTRUCTIONS:")
    for instruction in instructions:
        instruction.print()
        instruction_row = [instruction.to_html(), instruction.stages["issue"], instruction.stages["read_op"], instruction.stages["exec_begin"], instruction.stages["exec_end"], instruction.stages["write_back"]]
        instructions_table.append(instruction_row)
    
    logging.debug("\nREGISTERS:")
    logging.debug(result)
    for key, value in result.items():
        regs_table.append([key, value])

    logging.debug("\nFUNCTIONAL UNITS:")
    logging.debug("unit\tbusy\top\tfi\tfj\tfk\tqj\tqk\trj\trk")
    for unit in ld_units:
        unit[0].print()
        unit_row = unit[0].to_html()
        units_table.append(unit_row)
    for unit in al_units:
        unit[0].print()
        unit_row = unit[0].to_html()
        units_table.append(unit_row)

    html += '<h2>SCOREBOARD</h2>'

    html += '<div>'
    html += '<table align="left" width="100%">'
    html += '<tr>'
    for item in header_inst:
        html += '<th>' + str(item) + '</th>'
    html += '</tr>'

    for row in instructions_table:
        html += '<tr>'
        for item in row:
            html += '<td>' + str(item) + '</td>'
        html += '</tr>'
    html +=' </table>'
    html += '</div>'

    html += '<div style = "clear:both;"></div>'

    html += '<div>'
    html += '<table align="left" width="100%">'
    html += '<tr>'
    for item in header_regs:
        html += '<th>' + str(item) + '</th>'
    html += '</tr>'

    for row in regs_table:
        html += '<tr>'
        for item in row:
            html += '<td>' + str(item) + '</td>'
        html += '</tr>'
    html +=' </table>'
    html += '</div>'

    html += '<div style = "clear:both;"></div>'

    html += '<div>'
    html += '<table align="left" width="100%">'
    html += '<tr>'
    for item in header_units:
        html += '<th>' + str(item) + '</th>'
    html += '</tr>'

    for row in units_table:
        html += '<tr>'
        for item in row:
            html += '<td>' + str(item) + '</td>'
        html += '</tr>'
    html +=' </table>'
    html += '</div>'

    html += '<div style = "clear:both;"></div>'

def unit_available(instruction):
    """ Checks if there's an available functional unit
    
    Arguments:
        instruction {Instruction} -- Instruction object
    
    Returns:
        Unit  -- Reference to the available unit, if it exists
    """
    global ld_units
    global al_units

    if (instruction.op in memory_operations):
        for unit in ld_units:
            FU = unit[0]
            if (not FU.busy):
                return unit
    elif (instruction.op in arithmetic_operations):
        for unit in al_units:
            FU = unit[0]
            if (not FU.busy):
                return unit
    return None


def issue(instruction):
    """ Issue an instruction to the pipeline
    
    Arguments:
        instruction {Instruction} -- Instruction to be issued
    
    Returns:
        Boolean -- Issue was successful or not
    """
    global clock

    # wait until (!Busy[FU] AND !Result[dst])
    # check if unit is available
    unit = unit_available(instruction)

    if (unit == None):
        return False

    # check if result register is available (WAW)
    if (instruction.dst != None):
        if (result[instruction.dst]):
            return False
    
    FU = unit[0]
    # issue instruction to functional unit
    FU.busy = True
    FU.op = instruction.op
    FU.fi = instruction.dst
    FU.fj = instruction.src1
    FU.fk = instruction.src2
    
    if (instruction.src1 not in result.keys()):
        FU.qj = None
    else:
        FU.qj = result[instruction.src1]
    
    if (instruction.src2 not in result.keys()):
        FU.qk = None
    else:
        FU.qk = result[instruction.src2]

    if (FU.qj):
        FU.rj = True
    if (FU.qk):
        FU.rk = True

    # set this instruction as being used by functional unit
    unit[1] = instruction

    # set result register as being used
    result[instruction.dst] = unit[0].name

    # mark current clock as ISSUE
    instruction.stages["issue"] = clock
    # advance stage
    instruction.current_stage = "read_op"

    return True


def read_operands(unit):
    """ Read operands for an instruction
    
    Arguments:
        unit {[Unit, Instruction]} -- Unit and Instruction to be checked
    
    Returns:
        Boolean -- Read operands was successful or not
    """

    FU = unit[0]
    instruction = unit[1]

    # check if we have to wait
    if ((FU.rj) or (FU.rk)):
        return False
    
    # mark current clock as ISSUE
    instruction.stages["read_op"] = clock
    # advance stage
    instruction.current_stage = "exec_begin"

    return True


def execute(unit):
    """ Execution stage for instruction, applies
        clock delay if necessary, depending on the
        instruction type
    
    Arguments:
        unit {[Unit, Instruction]} -- Unit and Instruction to be checked
    """
    # store current cycle in current stage
    # of the instruction this FU is handling
    global instruction_index
    global instructions
    global clock
    
    instruction = unit[1]

    if (instruction.current_stage == "exec_begin"):
        # mark current clock as ISSUE
        instruction.stages["exec_begin"] = clock
        # advance stage
        instruction.current_stage = "exec_end"
        # check if we have to wait or we can fill exec_end already
        future_clock = clock + 1
        if (instruction.op in memory_operations):
            if (delay_ldu == 0):
                instruction.stages["exec_end"] = clock
                instruction.current_stage = "write_back"
        elif (instruction.op in arithmetic_operations):
            if (delay_alu == 0):
                instruction.stages["exec_end"] = clock
                instruction.current_stage = "write_back"

    elif (instruction.current_stage == "exec_end"):
        if (instruction.op in memory_operations):
            if (clock - instruction.stages["exec_begin"] == delay_ldu):
                instruction.stages["exec_end"] = clock
                instruction.current_stage = "write_back"
        elif (instruction.op in arithmetic_operations):
            if (future_clock - instruction.stages["exec_begin"] == delay_alu):
                instruction.stages["exec_end"] = clock
                instruction.current_stage = "write_back"


def write_back(unit):
    """ Write results and removes instruction from pipeline
    
    Arguments:
        unit {[Unit, Instruction] -- Unit and Instruction to be checked
    
    Returns:
        Boolean -- Success
    """
    global clock
    global finished_counter

    instruction = unit[1]
    unit = unit[0]

    # check all functional units for availability of source operands (WAR)
    for functional_unit in (ld_units + al_units):
        FU = functional_unit[0]
        # wait until (∀f {(Fj[f]≠Fi[FU] OR Rj[f]=No) AND (Fk[f]≠Fi[FU] OR Rk[f]=No)})
        # if (not ((FU.fj != unit.fi or (FU.rj == False)) and (FU.fk != unit.fi or (FU.rk == False)))):
            # return False

    instruction.stages["write_back"] = clock
    instruction.current_stage = "finished"
    finished_counter += 1

    return True


def finished(unit):
    """ Clears functional unit after write-back
    
    Arguments:
        unit {Unit} -- Unit to be cleared
    """

    instruction = unit[1]
    unit = unit[0]

    # clear all functional units where this one is flagged as being used
    for functional_unit in (ld_units + al_units):
        FU = functional_unit[0] # functional unit I'm alerting
        if (FU.qj == unit.name):
            FU.rj = False
            FU.qj = None
        if (FU.qk == unit.name):
            FU.rk = False
            FU.qk = None
    
    # clear register being written
    result[unit.fi] = False
    # flag unit as free for using
    unit.busy = False

    instruction.stages["finished"] = clock


def loop():
    """ Runs pipeline simulation until stop condition
    
    Returns:
        Boolean -- False if reached end of simulation
    """
    global instruction_index
    global clock
    global html

    logging.debug("\n[CLOCK " + str(clock) + "]")
    html += '<h1>CLOCK ' + str(clock) + '</h1>'
    
    logging.debug("\nOPERATIONS:")
    html += '<h2>OPERATIONS</h2>'

    if (finished_counter == len(instructions)):
        logging.debug("FINISHED.")
        return False # code finished execution

    # execute instructions currently on pipeline
    # order by stage
    to_finish = []
    to_write = []
    to_execute = []
    to_read = []

    # group instructions in execution by their stage
    for functional_unit in (ld_units + al_units):
        if (functional_unit[0].busy):
            current_instruction = functional_unit[1]
            if (current_instruction.current_stage == "finished"):
                to_finish.append(functional_unit)
            elif (current_instruction.current_stage == "write_back"):
                to_write.append(functional_unit)
            elif (current_instruction.current_stage == "exec_begin"):
                to_execute.append(functional_unit)
            elif (current_instruction.current_stage == "exec_end"):
                to_execute.append(functional_unit)
            elif (current_instruction.current_stage == "read_op"):
                to_read.append(functional_unit)

    # execute current instruction
    for functional_unit in to_finish:
        finished(functional_unit)
        logging.debug("Finished with " + current_instruction.op)
        html += "<p>Finished with " + str(current_instruction.op) + "</p>"

    for functional_unit in to_write:
        if (write_back(functional_unit)):
            logging.debug("Write back for " + current_instruction.op)
            html += "<p>Write back for " + str(current_instruction.op) + "</p>"
        else:
            logging.debug("Failed to write back for " + str(current_instruction.op))
            html += "<p>Failed to write back for " + str(current_instruction.op) + "</p>"

    for functional_unit in to_execute:
        execute(functional_unit)

    for functional_unit in to_read:
        if (read_operands(functional_unit)):
            logging.debug("Read operands for " + str(current_instruction.op))
            html += "<p>Failed to write back for " + str(current_instruction.op) + "</p>"

        else:
            logging.debug("Failed to read operands for " + str(current_instruction.op))
            html += "<p>Failed to read operands for " + str(current_instruction.op) + "</p>"

    # try to issue new instruction
    if (instruction_index < len(instructions)):
        instruction = instructions[instruction_index]
        if (issue(instruction)):
            logging.debug("Issued " + instruction.op)
            html += "<p>Issued " + str(instruction.op) + "</p>"
            instruction_index += 1
        else:
            logging.debug("Can't issue " + instruction.op)
            html += "<p>Can't issue " + str(instruction.op) + "</p>"

    status()

    clock += 1

    return True


def parse_code(code):
    """ Parses source code to the simulation format
    
    Arguments:
        code {String} -- Source code read from .asm file
    """
    global instructions
    global instruction_index

    code = code.replace(",", "")
    for instruction in code.splitlines():
        instruction = instruction.split()
        if (len(instruction) <= 0):
            return
        op = instruction[0]
        arg1 = instruction[1]
        arg2 = instruction[2]
        if (len(instruction) > 3):
            arg3 = instruction[3]
        else:
            arg3 = None

        if (op == 'lw'):
            dest = arg1
            src1 = arg2.split('(')[1].replace(")", "")
            src2 = None
        elif (op == 'sw'):
            dest = None
            src1 = arg1
            src2 = arg2.split('(')[1].replace(")", "")
        else:
            dest = arg1
            src1 = arg2
            src2 = arg3

        logging.debug(str(instruction_index) + " " + str(op) + " " + str(dest) + " " + str(src1) + " " + str(src2))

        instructions.append(Instruction(instruction_index, op, dest, src1, src2))
        instruction_index += 1


def main(code, n_ldu, n_alu, d_ldu, d_alu):
    global clock
    global instruction_index
    global instructions
    global delay_alu
    global delay_ldu
    global html

    html += """<html><head>
    <!-- CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <link rel="stylesheet" type="text/css" href="/static/css/simulator.css">
    <link href="static/css/bare.min.css" rel="stylesheet">
    <!-- Favicon -->
    <link rel="shortcut icon" type="image/png" href="/static/images/S.png"/>

    <title>Scoreboarding</title>

    <body>

    <form method="get" action="/simulator/download">
        <button type="submit"><i class="fa fa-download"></i> Download dos resultados</button>
    </form>
</head>"""

    logging.debug("Parsing source code...")
    parse_code(code)

    init_ldu(n_ldu)
    init_alu(n_alu)
    delay_ldu = d_ldu
    delay_alu = d_alu

    instruction_index = 0
    while(loop()):
        pass
    status()

    html += """</body></html>"""

    with open('templates/results.html', 'w') as file:
        file.write(html)

