import xml.etree.ElementTree as XML
import sys
import frame_stack
import frame
import re
verbose = False  # TODO !!!only for debug
# TODO change all return values from bool to int - 0 means OK, other codes means something else - caused by jumps





class Interpreter:
    frame_stack = frame_stack.FrameStack()
    labels = dict()
    return_stack = [-1]
    global_frame = frame.Frame()
    temporary_frame = None
    data_stack = list()
    input_stream = None

    def __init__(self, input_redirected):
        if input_redirected:
            self.input_stream = input_redirected

    def get_input(self):
        if self.input_stream:
            with open(self.input_stream, "r") as file:
                return file.readline().replace("\n","")
        else:
            return input()


    def get_labels(self, path_to_input):
        """
        Method finds all labels and stores their names with their order number
        :param path_to_input: input file/STDIN
        :return: Nothing
        """
        #print("***GET_LABELS", file=sys.stderr)
        xml_tree = XML.parse(path_to_input)
        root = xml_tree.getroot()
        for instruction in root.iter("instruction"):
            #print(instruction.attrib["opcode"] == "LABEL")
            if instruction.attrib["opcode"] == "LABEL":
                if self.not_duplicit(instruction.text):
                    #print("HELDANI LABELU:", str(instruction.find("arg1").text), instruction.attrib["order"])
                    self.labels[str(instruction.find("arg1").text)] = int(instruction.attrib["order"])
                    #print("***GET_LABELS", self.labels)
                else:
                    return 52 # bad label

    def not_duplicit(self, label_name):
        "Private method, returns if label_name will be duplicit if added to labels dictionary."
        #print("NOT DUPLICIT", label_name in self.labels.keys())
        return not(label_name in self.labels.keys())

    def interpret_instruction(self, instruction, args):
        """Root method to whole interpreting. Actually, only runs switch and checks for errors :)"""
        #print(instruction.attrib["order"], instruction.attrib["opcode"], "***Doing interpretation***")
        jump = [False, None]
        instruction_done = self.switch_interpreting(instruction, jump, args)
        if verbose:
            print("GF:",self.global_frame.frame_variables)
            if self.temporary_frame:
                print("TF", self.temporary_frame.frame_variables)
            if self.frame_stack.frame_stack:
                print("LF-top:", self.frame_stack.top().frame_variables)

        if instruction_done == 0:
            if jump[0]:
                return jump[1]
            else:
                return int(instruction.attrib["order"])
        else:
            return instruction_done,  # tuple as indication of err

    def switch_interpreting(self, instruction, jump, args):
        """ Method switching to specific instruction interpretation based on instructions opcode."""
        opcode = instruction.attrib["opcode"]
        if opcode == "DEFVAR":
            for arg in instruction:
                if arg.tag == "arg1":
                    return self.defvar(self.get_value(arg.text))
            return 52 # chyba in XML
        elif opcode == "MOVE":
            return self.move(self.get_arg(instruction, 1), self.get_arg(instruction, 2))
        elif opcode in ("ADD", "SUB", "MUL", "IDIV"):
            return self.numerical(self.get_arg(instruction, 2), self.get_arg(instruction, 3),
                                  self.get_arg(instruction, 1),operation=opcode)
        elif opcode in ("LT", "GT", "EQ"):
            return self.compare( self.get_arg(instruction, 2),self.get_arg(instruction, 3),self.get_arg(instruction, 1),
                                operation=opcode)
        elif opcode in ("AND","OR"):
            val = self.logic_compare(self.get_arg(instruction, 2), self.get_arg(instruction, 3),
                                     self.get_arg(instruction, 1), operation=opcode)
            if type(val) == bool:
                return 0
            else:
                return val
        elif opcode == "NOT":
            val = self.logic_compare(dst=self.get_arg(instruction, 1), first=self.get_arg(instruction, 2),
                                     second=None, operation=opcode)
            if type(val) == bool:
                return 0
            else:
                return val
        elif opcode == "STRI2INT":
            return self.str2int(self.get_arg(instruction, 1), self.get_arg(instruction, 2),
                                self.get_arg(instruction, 3))
        elif opcode == "CONCAT":
            return self.concat(self.get_arg(instruction, 1), self.get_arg(instruction, 2),
                               self.get_arg(instruction, 3))
        elif opcode == "GETCHAR":
            return self.getchar(self.get_arg(instruction, 1), self.get_arg(instruction, 2),
                                self.get_arg(instruction, 3))
        elif opcode == "SETCHAR":
            return self.setchar(self.get_arg(instruction, 1), self.get_arg(instruction, 2),
                                self.get_arg(instruction, 3))
        elif opcode in ("JUMPIFEQ", "JUMPIFNEQ"):
            ret_value = self.jumpif(self.get_arg(instruction, 1).text,
                                    condition=self.jump_compare(self.get_arg(instruction, 2), self.get_arg(instruction, 3)),
                                    negation=True if opcode == "JUMPIFNEQ" else False)
            if ret_value < 0:  # means
                    if ret_value == -1:
                        return 0
                    return -ret_value
            else:
                jump[0] = True
                jump[1] = ret_value
                return 0
        elif opcode == "JUMP":
            ret_value = self.jumpif(self.get_arg(instruction, 1).text, condition=True)
            if ret_value < 0:  # menas err
                    if ret_value == -1:
                        return 0
                    return -ret_value
            else:
                jump[0] = True
                jump[1] = ret_value
                return 0
        elif opcode == "INT2CHAR":
            return self.int2char(self.get_arg(instruction, 1), self.get_arg(instruction, 2))
        elif opcode == "READ":
            return self.read(self.get_arg(instruction, 1), self.get_arg(instruction, 2), args)
        elif opcode == "STRLEN":
            return self.strlen(self.get_arg(instruction, 1), self.get_arg(instruction, 2))
        elif opcode == "TYPE":
            return self.type(self.get_arg(instruction, 1), self.get_arg(instruction, 2))
        elif opcode == "CALL":
           ret_value = self.call(instruction)  # Because we need an order number of the instruction
           if ret_value < 0:  # menas err
                if ret_value == -1:
                    return 0
                return -ret_value
           else:
                jump[0] = True
                jump[1] = ret_value
                return 0
        elif opcode == "PUSHS":
            return self.pushs(self.get_arg(instruction, 1))
        elif opcode == "POPS":
            return self.pops(self.get_arg(instruction, 1))
        elif opcode == "WRITE":
            return self.write(self.get_arg(instruction))
        elif opcode == "LABEL":
            return 0
        elif opcode == "EXIT":
            #print("EEEEEEXXXXXXXXXXXXXIIIIIIIIIIIIIITTTTTTTTTTTTT",self.get_value(self.get_arg(instruction, 1)))
            exit(self.get_value(self.get_arg(instruction, 1)))
        elif opcode == "DPRINT":
            return self.dprint(self.get_arg(instruction, 1))
        elif opcode == "CREATEFRAME":
            return self.createframe()
        elif opcode == "PUSHFRAME":
            return self.pushframe()
        elif opcode == "POPFRAME":
            return self.popframe()
        elif opcode == "RETURN":
            ret_value = self.interpret_return()
            if ret_value == -1:  # menas err
                return 0
            else:
                jump[0] = True
                jump[1] = ret_value
                return 0
        elif opcode == "BREAK":
            return self.interpret_break(instruction)  # prints some info about instruction, so i give it whole
        else:
            return 52  # bad semantics

    def defvar(self, var_name):
        """Method for interpretation DEFVAR opcode. """
        prefix = var_name[0:2]
        if prefix == "GF":
            self.global_frame.declare_var(var_name[3:])
            return 0
        elif prefix == "LF":
            self.frame_stack.top().declare_var(var_name[3:])
            return 0
        elif prefix == "TF":
            self.temporary_frame.declare_var(var_name[3:])
            return 0
        else:
            return 55 # rámec neexistuje

    def setvar(self, dst, src, var_type):
        #print("//////////setvar", src, file=sys.stderr)
        if type(dst) == XML.Element:
            dst = dst.text
        prefix = dst[0:2]
        src_value = self.get_value(src)
        if prefix == "GF":
            self.global_frame.set_var(dst[3:], src_value, var_type)
        elif prefix == "LF":
            self.frame_stack.top().set_var(dst[3:], src_value, var_type)
        elif prefix == "TF":
            self.temporary_frame.set_var(dst[3:], src_value, var_type)

    def move(self, dst, src):
        """MOVE dst src"""
        #print("MOVE", self.is_defined(src), dst.attrib["type"] != "var",self.is_declared(dst), dst.text)
        if self.is_defined(src) and (dst.attrib["type"] != "var" or self.is_declared(dst)):
            self.setvar(dst.text, src.text, src.attrib["type"])
            return 0
        return 53 #bad var

    def numerical(self, first, second, dst, operation=None):
        print("***NUM ",operation, file=sys.stderr)
        print(first.attrib["type"], first.text, self.is_defined(first) , file=sys.stderr)
        if first.attrib["type"] == "var" and not self.is_defined(first): return 54
        if second.attrib["type"] == "var" and not self.is_defined(second): return 54
        print(dst.attrib["type"] != "var" , not self.is_declared(dst),dst, file=sys.stderr)
        if dst.attrib["type"] != "var" or not self.is_declared(dst): return 54
        try:
            first_value = int(self.get_value(first))
            second_value = int(self.get_value(second))
        except ValueError:
            print("instruction {0}: Invalid type of arguments.".format(operation), file=sys.stderr)
            return 53  # bad arg types
        if operation == "ADD":
            self.setvar(dst, first_value + second_value, "int")
        elif operation == "SUB":
            self.setvar(dst, first_value - second_value, "int")
        elif operation == "MUL":
            self.setvar(dst, first_value * second_value, "int")
        elif operation == "IDIV":
            if second_value == 0:
                return 57  # zero division
            else:
                self.setvar(dst, first_value // second_value, "int")
        return 0


    def compare(self, first, second, dst, operation=None):
       #print("***compare gt lt eq", first.attrib["type"] , second.attrib["type"], first.attrib["type"] not in ("int", "bool", "string") )
        if (first.attrib["type"] != second.attrib["type"]) or (first.attrib["type"] not in ("int", "bool", "string")):
            return 53 # bad operand type
        first_value = self.get_value(first)
        second_value = self.get_value(second)
        if operation == "LT":
            if first_value < second_value:
                self.setvar(dst, "true","bool")
            else:
                self.setvar(dst, "false", "bool")
        elif operation == "GT":
            if first_value > second_value:
                self.setvar(dst, "true","bool")
            else:
                self.setvar(dst, "false", "bool")
        elif operation == "EQ":
            if first_value == second_value:
                self.setvar(dst, "true","bool")
            else:
                self.setvar(dst, "false", "bool")
        return 0

    def jump_compare(self, first, second):
        #print("*++++++++", first.text, file=sys.stderr)
        first_value = self.get_value(first)
        second_value = self.get_value(second)
        #print("***jump_compare", first_value, second_value, type(first_value), type(second_value), file=sys.stderr)
        if type(first_value) == type(second_value):
            if first_value == second_value:
                return True
            else: return False
        else: return 53 # bad types

    def logic_compare(self, first, second=None, dst=None, operation=None):
        #print("*** logic compare", first.attrib["type"] != "bool")
        if first.attrib["type"] != "bool" or (second and second.attrib["type"] != "bool"):
            return 53  # bad type
        else:
            if operation == "AND":
                if self.get_value(first) == self.get_value(second) == True:
                    self.setvar(dst,"true", "bool")
                else:
                    self.setvar(dst,"false", "bool")
            elif operation == "OR":
                if self.get_value(first) == self.get_value(second) == False:
                    self.setvar(dst, "false", "bool")
                else:
                    self.setvar(dst,"true", "bool")
                    print(self.global_frame.frame_variables)
            elif operation == "NOT":
                #print("NOT a neco se sere")
                if self.get_value(first) == True:
                    self.setvar(dst, "false", "bool")
                else:
                    self.setvar(dst, "true", "bool")
            return True

    def str2int(self, dst, src, position):
        #print("SSSSSSSSSSSSSstring to int",dst, src, position )
        position_value = self.get_value(position)
        string = self.get_value(src)
        #print("ssss",string[position_value], type(string[position_value]))
        if string and position_value < len(string):
            self.setvar(dst, ord(string[position_value]), "int")
            return 0
        else: return 58  # Chybná práce s řetězcem

    def concat(self, dst, src1, src2):
        string1 = self.get_value(src1)
        string2 = self.get_value(src2)
        if string1 and string2:
            self.setvar(dst, string1+string2, "string")
            return 0
        else: return 58

    def getchar(self, dst, src, position):
        position_value = self.get_value(position)
        string = self.get_value(src)
        if string and position_value < len(string):
            self.setvar(dst, string[position_value], "int")
            return 0
        else:
            return 58  # Chybná práce s řetězcem

    def setchar(self, dst, position, src):
        """src may be a string -> only first char is used"""
        string_to_modif = self.get_value(dst)
        if src.attrib["type"] == "string":
            source_string: str = self.get_value(src)
        else:
            return 53  # bad op type
        if source_string and len(source_string) > position:
            char_which_replaces = source_string[position]
        elif source_string:
            char_which_replaces = source_string[0]
        else:
            return 58
        new_string = string_to_modif[:position]+char_which_replaces+string_to_modif[position+1:]
        self.setvar(dst, new_string,"string")

    def jumpif(self, label, condition=False, negation=False):
        #print("*** JUMPIF", condition, label, file=sys.stderr)
        if negation:
            condition = not condition
        if condition:
            if label in self.labels.keys():
                return self.labels[label]
            else:
                return -52 # bad label
        else:
            return -1

    def int2char(self, dst, ord_src):
        #print("IIIIIIIIIIIII", dst, ord_src)
        ord_value = self.get_value(ord_src)
        try:
            self.setvar(dst, chr(ord_value), "string")
        except ValueError:
            print("Ordinal value out of range for Unicode", file=sys.stderr)
            return 58
        except TypeError:
            print("Bad ordinal value", file=sys.stderr)
            return 58
        return 0

    def read(self, dst, type, args):
        src = self.get_input()
        if not src or \
           type == "bool" and src not in ("true", "false") or\
           type == "int" and not str.isdigit(src):
            return 53
        else:
            self.setvar(dst, src, type)
            return 0

    def strlen(self, dst_len, string):
        #print("RRRRRRRRRRRR", string)
        string_value = self.get_value(string)
        self.setvar(dst_len, len(string_value), "int")
        return 0

    def interpret_break(self, instruction):
        """Nothing to do with break in cycle. Just prints to stderr some interesting info :)
         Param instruction is here only for this info"""
        print("Instruction: {0}\n".format(instruction.tag), file=sys.stderr)
        return 0

    def call(self, instruction):
        """call with support of return"""
        #print("CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCall",instruction.attrib["order"] )
        label = self.get_arg(instruction, 1)
        if label.text in self.labels.keys():
            self.return_stack.append(int(instruction.attrib["order"]))
            return self.labels[label.text]
        else:
            return -52 # bad label

    def interpret_return(self):
        """Just return. """
        #print("RETURN????????????????????????????????????????", len(self.return_stack))
        if len(self.return_stack) == 1:
            return -1
        #print("RRRRRRRRReturn", self.return_stack)
        return self.return_stack.pop(-1)

    def popframe(self):
        self.temporary_frame = self.frame_stack.pop_frame()
        if not self.temporary_frame:
            return 55
        return 0

    def pushframe(self):
        if verbose:
            print("GF:",self.global_frame.frame_variables)
            if self.temporary_frame:
                print("TF", self.temporary_frame.frame_variables)
            if self.frame_stack.frame_stack:
                print("LF-top:", self.frame_stack.top().frame_variables)
        if not self.temporary_frame:
            return 55  # bad work with frames
        self.frame_stack.push_frame(self.temporary_frame)
        self.temporary_frame = None
        if verbose:
            print("GF:",self.global_frame.frame_variables)
            if self.temporary_frame:
                print("TF", self.temporary_frame.frame_variables)
            if self.frame_stack.frame_stack:
                print("LF-top:", self.frame_stack.top().frame_variables)
        return 0

    def createframe(self):
        self.temporary_frame = frame.Frame()
        if verbose:
            print("GF:",self.global_frame.frame_variables)
            if self.temporary_frame:
                print("TF", self.temporary_frame.frame_variables)
            if self.frame_stack.frame_stack:
                print("LF-top:", self.frame_stack.top().frame_variables)
        return 0

    def dprint(self,message):
        print(message.text, file=sys.stderr)
        return 0

    def convert_escapes(self, text):
        if type(text) != str:
            return text

        escapes = re.findall(r"\\[\d]{3}", text)
        for escape in escapes:
            if escape[1] == "0":
                text = text.replace(escape, chr(int(escape[2:])))
            else:
                text = text.replace(escape, chr(int(escape[1:])))

        return text


    def write(self, src):
        #print("***+++---///+++---***///WRITE",self.get_value(src),src)
        raw_text = self.get_value(src)
        print(self.convert_escapes(raw_text),end="", sep="")
        return 0

    def pushs(self, src):
        #print("QQQQEEEEEEEEEEEEEEEEEEE", src.attrib, src.text)
        value_and_type = str(self.get_value(src)), str(self.get_type(src))

        if value_and_type:
            self.data_stack.append(value_and_type)
            #print("EEEEEEEEEEEEEEEEEEE", self.data_stack)
            return 0
        else:
            return 54  # variable doesnt exist

    def pops(self, dst):
        #print("EEEEEEEEEEEEEEEEEEE POPS", self.data_stack, dst)
        try:
            popped_value = self.data_stack.pop(-1)
            #print("poped", popped_value)
        except IndexError:
            return 56
        #print("WWWWWW", popped_value[0], popped_value[1])
        self.setvar(dst, popped_value[0], popped_value[1])
        return 0


    def type(self, dst, src):
        """ If var, return expected, if var not None, returns True, else returns False"""
        #print("PPPPPPPPPP Type: ", dst, src.attrib["type"],self.get_value(src))
        if src.attrib["type"] == "var":
            value = self.get_value(src)
            if value == "true" or value == "false":
                self.setvar(dst, "bool", "string")
            elif str.isdigit(value):
                self.setvar(dst, "int   ", "string")
            elif value == None:
                self.setvar(dst, "nil", "string")
            else:
                self.setvar(dst, "string", "string")
        else:
            self.setvar(dst, src.attrib["type"], "string")
        return 0

    def get_type(self, src):
        """ gets the type, equivalent to type() in python"""
        #print("PPPPPPPPPP get_Type: ",  src.attrib["type"],self.get_value(src))
        if src.attrib["type"] == "var":
            value = self.get_value(src)
            if value == "true" or value == "false":
                return "bool"
            elif type(value) == int or str.isdigit(value):
                return "int"
            elif value == None:
                return "nil"
            else:
                return "string"
        else:
            return src.attrib["type"]

    def is_declared(self, var):
        """ If var, return expected, if var not None, returns True, else returns False"""
        if var.attrib["type"] != "var":
            return True
        else:
            prefix = var.text[0:2]
            if prefix == "GF":
                return self.global_frame.is_declared(var.text[3:])
            elif prefix == "LF":
                return self.frame_stack.top().is_declared(var.text[3:])
            elif prefix == "TF":
                return self.temporary_frame.is_declared(var.text[3:])
            else:
                return False

    def is_defined(self, var):
        """ If var, return expected, else return True"""
        if var.attrib["type"] != "var":
            return True
        else:
            prefix = var.text[0:2]
            if prefix == "GF":
                return self.global_frame.is_defined(var.text[3:])
            elif prefix == "LF":
                return self.frame_stack.top().is_defined(var.text[3:])
            elif prefix == "TF":
                return self.temporary_frame.is_defined(var.text[3:])
            else:
                return False

    def get_value(self, var):
        if type(var) == str and var.isdigit():
            return int(var)
        if type(var) == int or \
           type(var) == str or \
           type(var) == bool:
            return var
        else:
            var_type = var.attrib["type"]
            if var_type == "var": #get the right frame and get a value from it
                prefix = var.text[0:2]
                if prefix == "GF":
                    #print(var.text)
                    return self.global_frame.get_var(var.text[3:])["value"]
                elif prefix == "LF":
                    return self.frame_stack.top().get_var(var.text[3:])["value"]
                elif prefix == "TF":
                    return self.temporary_frame.get_var(var.text[3:])["value"]
                else:
                    return None
            elif var_type == "type" or var_type == "label" or var_type == "string" or var_type == "int":
                if var_type == "int" and var.text.isdigit():
                    return int(var.text)
                else:
                    return var.text
            elif var_type == "nil":
                return None  # TODO BEWARE: *** None == nil ***
            elif var_type == "bool":
                if var.text == "true":
                    return True
                else:
                    return False
            else:
                return None

    def get_arg(self,instruction,arg_num=1):
        return instruction.find("arg"+str(arg_num))