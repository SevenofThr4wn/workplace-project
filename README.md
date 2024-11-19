This flask web application was designed to be used as a tool for workplace managers/supervisors to regulate and maintain healthy working conditions within an in-closed work environment. The system uses a Raspberry Pi with a wired Temperature Sensor to record and send temperatures of the surrounding environment and write the data into a JSON file. The system also uses the Australian Bureau of Meteorology API to fetch the latest Temperature, Humidity and apparent temperature and displays the above data onto a simple web interface. 

> [!IMPORTANT]
> The system was intentionally designed to be operated on the raspberry pi, and when developing the system, the Linux fork used did not have access to the internet, so use at your own peril. Additionally, the source code is still a work in progress, I will be updating the project at regular intervals.

More documentation will come soon when more progress has been made.

If you desire, i am more than happy for people to modify my work, I also encourage people who do modify the source code to give any feedback so I can improve these small projects!

if you have any inquires please DM me on Discord, where my ID is sevenofthr4wn


#Using the Project on Windows 10/11

It is possible to use this project on Windows 10/11 because it was devloped on a Windows machine. To start the Flask web server, go into the PyCharm console, and type: "flask run". This will launch the webpage which can be accessed via the local url when executing the command.
