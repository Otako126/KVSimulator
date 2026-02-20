from modules.base import LadderModuleBase


class Module(LadderModuleBase):
    name = "X"

    def execute(self, ctx):
        done = ctx.mem.read_bits("MR", 1, 1, source="ladder:X")[0]
        if done:
            ctx.mem.write_words("DM", 101, [1], source="ladder:X")
