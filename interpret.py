import argparse
import interpret_class as INPR
import sys
import xml.etree.ElementTree as XML

descr_string = """Application to interpret XML representation of IPPcode19."""

parser = argparse.ArgumentParser(description=descr_string)
parser.add_argument("--source", dest="source", help="Path to input XML file", default="STDIN")
parser.add_argument("--input", dest="input", help="Path a file with inputs used as STDIN inputs", default=None)
args = parser.parse_args()
if args.source == args.input == "STDIN":
    print("At least one argument of --input, --source must be specified!", file=sys.stderr)
    exit(10)

# TODO check if args.source exists!
interpret = INPR.Interpreter(args.input)
interpret.get_labels(args.source)

xml_tree = XML.parse(args.source)  # Get the XML tree
root = xml_tree.getroot()

instruction_count = len(root.getchildren())-1
current = 0
instructions = root.getchildren()
instructions = sorted(instructions, key=lambda x: int(x.attrib["order"]))

while current <= instruction_count:
    #print("++++++++++++++++++++++++++++++++++++++++++", instructions[current].attrib["opcode"],  "****")
    return_value = interpret.interpret_instruction(instructions[current], args)
    #print("++++++++++++++++++++++++++++++++++++++++++", instructions[current].attrib["opcode"], return_value, "+++++")
    #print("_____________________________________________________________________________________________", type(return_value), return_value)
    if type(return_value) == int:
        next_instruction = return_value
        #print("ret:", return_value)
    elif type(return_value) == tuple:
        if(return_value[0]) > 0:
            print("An error has occured", file=sys.stderr)
            exit(return_value[0])
        else:
            next_instruction = return_value[0]
    else:
        print("An error has occured – order number of next instruction was not given properly", file=sys.stderr)
        exit(99)
    current = next_instruction
