Feature: Commit changes to git after updating component
  In oreder to have git history of changes
  As a maintainer
  I want to perform git commit after each component update


  Scenario: Update version in defined files for component
     Given New version of component is set in defined files in git repo
      When script is run in update mode with git-commit parameter
      Then there is same number of git commits than components defined