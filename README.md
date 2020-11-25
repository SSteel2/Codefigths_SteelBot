# Codefigths_SteelBot
Visma Codefights BuildStuff 2020 competition winning bot.

Data folder contains analysis files for opponents.

Main idea of the algorithm is to attack most statiscally viable spots where opponent might not defend and defend where it has most attacked.
It only takes last 5 moves into account, in order to react quickly enough to opponent strategy changes. Each area attack/defend chance is weighted towards more valuable areas.

Check pattern and abuse pattern functions try to figure out if opponent is acting according to a sequence, if so - algorithm blocks all incoming attacks and goes for highest viable value areas for damage.