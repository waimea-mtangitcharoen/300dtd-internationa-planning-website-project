# Sprint 1 - A Working UI Prototype


## Sprint Goals

Develop a prototype that simulates the key functionality of the system, then test and refine it so that it can serve as the model for the next phase of development in Sprint 2.

[Figma](https://www.figma.com/) is used to develop the prototype.


---

## Initial Database Design

This initial database design contains 5 tables: users, membership, votes, groups, events, and options. These tables are linked together either by 1:N or N:N relatioship, and work together to allow information about users, groups, and events to be stored in the database and allow some actions to happen.

![Original DB design](screenshots/0_DB.png)


### Required Data Input

Admin users will provide:
- Information about the group (via create group form)
- Information about events (via add event form)

Normal users will provide:
- Basic personal information of the international student leaders (name, username, password) (via sign-up form)

### Required Data Output

Admin users will see:
- Name/profile of the user
- List of groups (that they are part of or have created)
- List of events associate to that group, with details/description and date shown.
- Results from the poll-vote and usernames of normal users

Normal users will see:
- List of groups (that they are part of)
- List of events assocaite to each group, with details/description and date shown.
- Results from the poll-vote and usernames of normal users.

Note that the data output for both types of users are very similar. However, admin users are capable to do more actions than normal users (some buttons or functionality will only appear for admin users).


### Required Data Processing

Users can only access the website only if they can log-in. So, username and password input via log-in form must be compared to what is stored in users table of the database.

List of groups will be displayed differently for each user, as they are part of different group. So, a query is required to run though the membership table and match the user id with the group id.

For the list of events for each group, the database must sorted only events with the "group_id" that match the "id" of the groups table.

## Final Database design

After talking to my end-users (other international students leaders), they prefer entering a code to join a group, rather than admin inviting people into the group when he/she create a group.

![Final DB design](screenshots/1_DB.png)

A new field "code" has been added to the group table of the database. This is to store the unique code generated for each group and make sure that they do not match.


---

## UI 'Flow'

The first stage of prototyping was to explore how the UI might 'flow' between states, based on the required functionality.

This Figma demo shows the initial design for the UI 'flow':

**FIGMA FLOW - PLACE THE FIGMA EMBED CODE HERE - MAKE SURE IT IS SET SO THAT EVERYONE CAN ACCESS IT**

### Testing

Replace this text with notes about what you did to test the UI flow and the outcome of the testing.

### Changes / Improvements

Replace this text with notes any improvements you made as a result of the testing.

*IMPROVED FIGMA FLOW - PLACE THE FIGMA EMBED CODE HERE - MAKE SURE IT IS SET SO THAT EVERYONE CAN ACCESS IT*


---

## Initial UI Prototype

The next stage of prototyping was to develop the layout for each screen of the UI.

This Figma demo shows the initial layout design for the UI:

*FIGMA PROTOTYPE - PLACE THE FIGMA EMBED CODE HERE - MAKE SURE IT IS SET SO THAT EVERYONE CAN ACCESS IT*

### Testing

Replace this text with notes about what you did to test the UI flow and the outcome of the testing.

### Changes / Improvements

Replace this text with notes any improvements you made as a result of the testing.

*FIGMA IMPROVED PROTOTYPE - PLACE THE FIGMA EMBED CODE HERE - MAKE SURE IT IS SET SO THAT EVERYONE CAN ACCESS IT*


---

## Refined UI Prototype

Having established the layout of the UI screens, the prototype was refined visually, in terms of colour, fonts, etc.

This Figma demo shows the UI with refinements applied:

*FIGMA REFINED PROTOTYPE - PLACE THE FIGMA EMBED CODE HERE - MAKE SURE IT IS SET SO THAT EVERYONE CAN ACCESS IT*

### Testing

Replace this text with notes about what you did to test the UI flow and the outcome of the testing.

### Changes / Improvements

Replace this text with notes any improvements you made as a result of the testing.

*FIGMA IMPROVED REFINED PROTOTYPE - PLACE THE FIGMA EMBED CODE HERE - MAKE SURE IT IS SET SO THAT EVERYONE CAN ACCESS IT*


---

## Sprint Review

Replace this text with a statement about how the sprint has moved the project forward - key success point, any things that didn't go so well, etc.

