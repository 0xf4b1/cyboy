# cyboy
An experimental gameboy emulator written in python

An experimental gameboy emulator written in python. It emulates the LR35902 CPU where most of its instructions are generated according to the structure of the instruction set. It uses curses text-mode output, so you can play directly in your terminal! But the drawing is quite resource consuming.

Roms like _Tetris_ or _Super Mario Land_ look okay, but many others will not work at the current state.

## Usage

	$ python cyboy.py <rom>

For better performance use `PyPy`:

	$ pypy3 cyboy.py <rom>

### Implemented

- CPU with full LR35902 instruction set
- MMU (partly)
- Display (partly) and output via curses
- Controls and input via keyboard

### Unimplemented

- Emulation speed, frame limiting
- Display windows
- MBC RAM, game saving
- Timers
- Sound
- more ...

## Resources

- http://pastraiser.com/cpu/gameboy/gameboy_opcodes.html
- http://problemkaputt.de/pandocs.htm
- http://marc.rawer.de/Gameboy/Docs/GBCPUman.pdf
- https://github.com/Baekalfen/PyBoy
