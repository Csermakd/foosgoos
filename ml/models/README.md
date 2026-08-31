# Trained weights live here

These files are NOT in git - they are large binaries that change every
time you retrain. Download them from the Modal volume after training:

    modal volume get foosgoos-scout-weights     <path> ./models/gameplay_v1.pt
    modal volume get foosgoos-architect-weights <path> ./models/table_v1.pt

The filenames must match `SCOUT_MODEL_PATH` and `ARCHITECT_MODEL_PATH`
in `../config.py`.

Keep the previous version around when you retrain (`gameplay_v0.pt`), so
that when the new one turns out worse on real footage you can put the old
one back in one command instead of waiting on another training run.
