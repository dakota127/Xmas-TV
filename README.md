# Xmas TV
This is a fun project.

I recently built what I call a Christmas TV based on a Raspberry Pi and Volumio-Software.
When I came across this lovely TV (see pic) in a shop I had the idea to beef it up with a Pi based musicplayer. The device was originally able to play about 6 christmas songs through a one inch speaker that was hooked up to a small circuit board.
The lovely 3D winter scenery ist illuminated with a number of led’s. A small train runs around in a circle with a tunnel. Just a tad kitschy but lovely. I call it Christmas TV.
So here is what I ended up with: I added a frontpanel with a number of pushbuttons and a backpanel with switches. The Pi is stacked with a HiFiBerry DAC+ and a Mini Jambox provides the sound output. It plays all my >200 xmas songs from Frank Sinatra, Elvis, Nat King Cole and many more (and plenty of Grateful Dead titles too). The mp3 songs are stored on a small usb stick.
The interface board carries all the resistors, the ADC chip für the volume and three connectors to the switches and led’s.
There are two python scripts (that could be combined into just one): one running several threads with callbacks for the pushbuttons. The other script initiates a shutdown if the shutdown pushbutton on the back panel is pressed. Before shutdown a 3 sec message is played: ‚thank you for listening, good bye‘.
The main scripts randomly plays a 6 sec. station identification: ‚all day, all night, Xmas TV, stay tuned for more‘ that I recorded on my Mac. This and the whole thing is just for fun

Project started in early 2014.

Documentation and code on GitHub. 
Documentation is in German, with English Abstract.  

Free to use, modify, and distribute with proper attribution.
Frei für jedermann, vollständige Quellangabe vorausgesetzt.

