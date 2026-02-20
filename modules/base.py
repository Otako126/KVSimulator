class LadderModuleBase:
    name = "base"

    def on_load(self, ctx):
        return None

    def execute(self, ctx):
        raise NotImplementedError

    def on_unload(self, ctx):
        return None
