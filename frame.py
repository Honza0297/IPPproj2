import sys


class Frame:
    frame_variables = None

    def __init__(self):
        self.frame_variables = dict()

    def set_var(self, variable, value, var_type):
       # print("**",self.frame_variables[variable], file=sys.stderr)
        self.frame_variables[variable]["value"] = value
        self.frame_variables[variable]["type"] = var_type
        if variable not in self.frame_variables.keys() or not self.frame_variables[variable]["defined"]:
            self.frame_variables[variable]["defined"] = True

    def declare_var(self, variable):
        if variable not in self.frame_variables.keys():
            self.frame_variables[variable] = {"type": None, "defined": False, "value": None}
        else:
            print("Redeclaration err", file=sys.stderr)

    def get_var(self, variable):
        #print("*******get_var in frame", variable, self.frame_variables)
        try:
            return self.frame_variables[variable]
        except KeyError:
            print("KeyError during get_var. Need to handle err probably undefined var")
            print(variable)
            return 0.  # Why float? not supported by ippcode by default, so it can be a sign of an error

    def is_declared(self,variable):
         # print("***frame is_declared", variable, self.frame_variables.keys(),  file=sys.stderr)
        return variable in self.frame_variables.keys()

    def is_defined(self,variable):
        # print("***frame is_Defined", variable, file=sys.stderr)
        if self.is_declared(variable):
            return self.frame_variables[variable]["defined"]