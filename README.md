# Recall
Recall provides a library of useful classes when implementing the "write" side
of a CQRS system with event sourcing. It currently has service locators for most
things to provide some degree of inversion of control, a memento-like repository
for dealing with Aggregate Roots in a DDD-way, and several interfaces for adding
your own Event & Snapshot stores and Event routers.

## CQRS
Command/Query Responsibility Segregation is a fancy-sounding term for what turns
out to be this elegant, and scalable way to design a service (within a Bounded
Context). It goes beyond Bertrand Meyer's admonition to separate Commands and
Queries within objects and makes them separate models: a Command-only, "write"
model and a Query-only "read" model. Turns out, this simple extension of Meyer
has some dramatic implications for the ability to scale a system while
providing the Availability and Partition Tolerance (and Eventual Consistency).

A "write" model with pure Commands (only changes state) can be implemented in
such a way that you never have to wait for the command to complete. This model
can also have it's own data store, optimized for writing. Likewise a "read"
model with pure Queries (only returns state) can have it's own read-optimized
data store, say, denormalized into "view" tables where every read simply returns
a single record.

## Event Sourcing
Building on top of CQRS, your write model could actually just be a sequence of
all the events that happened to your domain model. This sequence would, in
effect, become a perfect audit log of your system.

## CQRS Links:
 - [Greg Young: Unshackle Your Domain](http://www.infoq.com/presentations/greg-young-unshackle-qcon08)
 - [Udi Dahan: CQRS](http://www.infoq.com/presentations/Command-Query-Responsibility-Segregation)

## Todo
 - [x] Add AMQP Event Router
 - [ ] Add an event replay tool
 - [ ] Add Redis Event Store
 - [ ] Add Memcached Snapshot Store

## spiralout/Tracks
This PHP library is the basis for Recall, but don't let PHP stop you. Tracks is
a well thought-out framework used in production every day. Not to mention that
spiralout is the guy that introduced me to CQRS.
