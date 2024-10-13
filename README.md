# TigerOutcomes
VCR for COS 333 project

# Preferred Setup for git
git config --global user.name [Username]  
git config --global user.email [Email]  
git config --global credential.helper store  
git config --global pull.rebase true  
git config --global rebase.autostash true  

# git commands
git pull/push  
    * Please always pull before pushing. It’s better to solve merge conflicts locally  
git add  
    * Don’t use this; stage in Sublime Merge instead  
git rebase -i HEAD~[n]  
    * Allows you to edit multiple previous commits  
        This is especially useful if you have many small commits that build upon one another  
    * Can use for editing commit messages (though you can do that in Sublime Merge)  
git status  
    * Can be used to check what your branch status is (i.e. if you are ahead/behind main)  

# Tools
VSCode  
    * Ctrl-Shift-P for command palette, search for ”Install 'code' command in PATH”  
        This will make git merge/squash/edit attempts redirect to VSCode  
Sublime Merge  
    * Ignore the “free trial” messages, they pop up but don’t do anything  
    * Settings -> Preferences -> Commit Messages -> Ruler, type in 50, 72  
        This makes it so that marking lines appear at 50 and 72 characters  
Linear  
    * Change Display to Board and open Issues tab (for full view)  

# Commits
Please follow the following format for commits  
  
[Name/Branch]: [Short, descriptive title (specifically, keep it under 50 characters)]  
[Longer description of commit]  
  
For an example, look at the second commit