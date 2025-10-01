class UniversalAdapter:
    """
    Ενιαίος adapter δύο τρόπων:
      - batch mode: το μοντέλο εκθέτει handleBatch(values) -> (scores, flags)
      - single mode: το μοντέλο εκθέτει handle_one(x) -> (score, flag)

    API:
      feed(x)  -> (vals, scores, flags) όταν κλείσει batch ή άμεσα στο single
                  ή (None, None, None) αν δεν έχει κλείσει batch ακόμη
      flush()  -> επιστρέφει τυχόν υπόλοιπα στο batch mode
    """
    def __init__(self, model, batch_size: int | None = None):
        self.model = model

        if hasattr(model, "handleBatch"):
            if not batch_size:
                raise ValueError("batch_size is required for batch models")
            self.mode = "batch"
            self.batch_size = int(batch_size)
            self.buf: list[float] = []
        elif hasattr(model, "handle_one"):
            self.mode = "single"
        else:
            raise RuntimeError("Model must define handleBatch(values) or handle_one(x)")

    def _normalize_pair(self, scores, flags):
        # Μετατροπή πιθανών numpy arrays σε λίστες και cast τύπων
        scores = [float(s) for s in list(scores)]
        flags = [int(f) for f in list(flags)]
        if len(scores) != len(flags):
            raise ValueError("scores and flags must have equal length")
        return scores, flags

    def feed(self, x_val: float):
        x = float(x_val)

        if self.mode == "single":
            out = self.model.handle_one(x)
            if not (isinstance(out, (tuple, list)) and len(out) == 2):
                raise TypeError("handle_one(x) must return (score, flag)")
            s, f = out
            s = float(s)
            f = int(f)
            return [x], [s], [f]

        # batch mode
        self.buf.append(x)
        if len(self.buf) < self.batch_size:
            return None, None, None

        vals = list(self.buf)
        self.buf.clear()

        scores, flags = self.model.handleBatch(vals)
        scores, flags = self._normalize_pair(scores, flags)

        if len(vals) != len(scores) or len(vals) != len(flags):
            raise ValueError("handleBatch outputs must match input length")

        return vals, scores, flags

    def flush(self):
        """Κλείσε τυχόν υπόλοιπα στο batch mode. Στο single δεν κάνει τίποτα."""
        if getattr(self, "mode", None) != "batch" or not self.buf:
            return None, None, None

        vals = list(self.buf)
        self.buf.clear()

        scores, flags = self.model.handleBatch(vals)
        scores, flags = self._normalize_pair(scores, flags)

        if len(vals) != len(scores) or len(vals) != len(flags):
            raise ValueError("handleBatch outputs must match input length")

        return vals, scores, flags

