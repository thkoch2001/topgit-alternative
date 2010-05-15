tnt is not topgit

An alternative to topgit, work in progress

I want to present a prototype at the Debian-Mini conference in june:

http://wiki.debconf.org/wiki/Miniconf-LT-Berlin/2010#2010-06-10_Thu




Synopsis
========

* cd into a testing GIT repo
* python PATH/TO/tnt.py

Commands
--------

* tnt init PATCHSET_BRANCH (inits PATCHSET_BRANCH with the current HEAD as root)
* tnt add PATCHSET_BRANCH (adds current branch as a patch branch)
* tnt status PATCHSET_BRANCH

TODO:

* tnt update PATCHSET_BRANCH (updates the current branch in the patchset)
* tnt rm PATCHSET_BRANCH (removes the current branch from the patchset)
* tnt export -f format PATCHSET_BRANCH DIR

This is my second piece of code in python, so there's a hell to learn for me!

Dependencies
============

Debian packages:

* python-yaml
* python-git


