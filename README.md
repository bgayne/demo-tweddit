#tweddit

A simple reddit/Twitter bot that tweets rising images from selected subreddits. 

This application implements threading and basic object oriented principles, encapsulating each API from the other, which ensures that a failure to recieve (or send) data from one API does not affect the normal function of the other. To achieve this, a queue with a basic mutex was implemented as well. 
