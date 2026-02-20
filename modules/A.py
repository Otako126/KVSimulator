from modules.base import LadderModuleBase


class Module(LadderModuleBase):
    name = "A"

    def execute(self, ctx):
        inp = ctx.mem.read_bits("R", 0, 1, source="ladder:A")[0]
        ctx.mem.write_bits("MR", 0, [1 if inp else 0], source="ladder:A")
