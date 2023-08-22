#!/usr/bin/python3.11

import xmltodict
import dataclasses
import typing as t
import click

FLAT: str = "♭"
SHARP: str = "♯"


@dataclasses.dataclass
class TimeSignature:
    upper: int
    lower: int

    @classmethod
    def parse(cls, measure_data: t.Dict) -> "TimeSignature":
        time_data = measure_data["attributes"]["time"]
        upper = int(time_data["beats"])
        lower = int(time_data["beat-type"])
        return TimeSignature(upper, lower)


@dataclasses.dataclass
class Note:
    value: str
    high: bool
    duration: float
    dotted: bool
    flat: bool = False
    sharp: bool = False

    @classmethod
    def parse(cls, note_data: t.Dict, time_signature_lower: int) -> "Note":
        value = note_data["pitch"]["step"]
        high = note_data["pitch"]["octave"] == "5" and value != "C"
        duration = int(note_data["duration"]) / 96
        dotted = "dot" in note_data.keys()
        note = Note(value, high, duration, dotted)
        if alter := note_data["pitch"].get("alter", None):
            if alter == -1:
                note.flat = True
            if alter == 1:
                note.sharp = True
        return note


@dataclasses.dataclass
class Measure:
    number: int
    notes: t.List[Note] = dataclasses.field(default_factory=list)
    ending: int = 0


@dataclasses.dataclass
class Tune:
    time_signature: TimeSignature
    measures: t.List[Measure]

    def as_str(self) -> str:
        tune_str: str = ""
        count: float = 0
        for measure in self.measures:
            if ending := measure.ending:
                tune_str += f"{ending}) "
            count = 0
            for note in measure.notes:
                length = note.duration + 0.5 if note.dotted else note.duration
                mid_point = (
                    self.time_signature.upper
                    if self.time_signature.lower <= 4
                    else int(self.time_signature.upper / 2)
                )
                if (
                    count > 0
                    and count <= mid_point
                    and count + length > mid_point
                ):
                    tune_str += " "
                count += length
                tune_str += note.value
                if note.high:
                    tune_str += "'"
                if length > 1:
                    tune_str += "- "
            if int(measure.number) < len(self.measures):
                tune_str += " | "
        tune_str = tune_str.replace("  ", " ")
        return tune_str


@click.command()
@click.argument("file")
def main(file: str) -> None:
    with open(file) as f:
        dct = xmltodict.parse(f.read())

    parts = dct["score-partwise"]["part"]
    if type(parts) == dict:
        measure_data = parts["measure"]
    else:
        measure_data = parts[0]["measure"]

    time_signature = TimeSignature.parse(measure_data[0])
    measures = []
    for measure in measure_data:
        ending_num = 0
        for barline in measure.get("barline", []):
            if type(barline) != dict:
                continue
            if not barline.get("ending", {}).get("@type", "") == "start":
                continue
            ending_num = int(barline["ending"]["@number"])
        number = measure["@number"]
        notes = []
        for note_data in measure["note"]:
            if type(note_data) == dict:
                notes.append(Note.parse(note_data, time_signature.lower))
        measures.append(Measure(number=number, notes=notes, ending=ending_num))

    tune = Tune(time_signature=time_signature, measures=measures)
    tune_str = tune.as_str()
    print(tune_str)


if __name__ == "__main__":
    main()
