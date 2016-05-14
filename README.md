# WorkFront-Issue-Archive

This code requires python 3.5 to run. You can get python from here. https://www.python.org/downloads/

If you already have python but are running 2.x branch you can either convert the code, or if you are using Anaconda you can create a 3.5 environment and switch to that to execute.

The script will ask you for your API Key, sub domain, and the ID number of the project you want to move from and to. The ID number is everything after "ID"= in the URL of the project. For example https://xxx.attask-ondemand.com/project/view?ID=56f3247504068461c284f24ba89cda0f. In this case the ID number would be "56f3247504068461c284f24ba89cda0f" without the quotes.

You can find your API Key in Workfront under setup->system->customer info. I'm fairly certain that you must be a system admin to have an API key. Techncially this script could be modified to accept a username and password instead, but I always use an API Key.

I'm OK with making minor changes to this script on request, so if you have any questions either msg me here or on Linkedin.


--------------
Note: This script will ask you if you want to run the live environment or sandbox. As of 5/12/16 something is broken in sanbox. Moving issues via the API or the standard user interface just hangs. Sanbox has been running super slow lately, so you will probably have to run this on live data. It only moves items.
