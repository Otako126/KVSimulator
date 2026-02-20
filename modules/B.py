from modules.base import LadderModuleBase


class Module(LadderModuleBase):
    name = "B"

    def execute(self, ctx):
        q, cv = ctx.plc.ctu("B_counter", bool(ctx.mem.read_bits("MR", 0, 1, source="ladder:B")[0]), 3)
        ctx.mem.write_words("DM", 100, [cv], source="ladder:B")
        ctx.mem.write_bits("MR", 1, [1 if q else 0], source="ladder:B")
