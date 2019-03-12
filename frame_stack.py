import frame
import sys

class FrameStack:
    frame_stack = list()

    def top(self):
        if self.frame_stack:
            return self.frame_stack[-1]
        else: return frame.Frame()

    def push_frame(self, input_frame):
        self.frame_stack.append(input_frame)

    def pop_frame(self):
        try:
            return self.frame_stack.pop()
        except IndexError:
            print("IndexError occured... :(", file=sys.stderr)
            return None
