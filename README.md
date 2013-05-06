# Recall
Recall provides a library of classes useful for implementing the "write" side of a CQRS system (with event sourcing). It currently has service locators for most things to provide some degree of inversion of control, a memento-like repository for dealing with Aggregate Roots in a [DDD](http://en.wikipedia.org/wiki/Domain-driven_design)-way, and several interfaces for adding your own Event routers and Event & Snapshot stores.

## CQRS
Command/Query Responsibility Segregation is a fancy-sounding term for what turns out to be this elegant, structured, and scalable way to design a service (within a Bounded Context). It goes beyond [Bertrand Meyer's admonition to separate Commands and Queries](http://en.wikipedia.org/wiki/Command%E2%80%93query_separation) within objects and makes them separate models: a Command-only, "write", model and a Query-only, "read", model. Turns out, this simple extension of Meyer has some dramatic implications for the ability to scale a system while providing Availability and Partition Tolerance (with Eventual Consistency -- [see CAP Theorem](http://en.wikipedia.org/wiki/CAP_theorem)).

A "write" model with pure Commands (only changes state) can be implemented in such a way that you never have to wait for the command to complete. This model can also have it's own data store, optimized for writing. Likewise a "read" model with pure Queries (only returns state) can have it's own read-optimized data store, say, denormalized into "view" tables where every read simply returns a single record.

## Event-Sourcing
Building on top of CQRS, the storage of your write model could actually just be a sequence of all the events that happened to your domain model. Aside from making it easy to publish these events for different kinds of analysis, this sequence would, in effect, become a _perfect_ audit log of your system.

## CQRS with Recall
Recall provides abstract implementations of Aggregage Roots, Domain Entities, Events, and Commands along with a Repository which handles saving & loading an AggregageRoot as well as writing to the Event stream, snapshotting the AR, and routing events. In short, the heavy-lifting of the "write" model. In the examples directory is a simple **planet_express.py** file which uses in-memory storage and a router to stdout and also a **mailing_tracker.py** which shows more advanced usage of the library. Tests will be forthcoming as well as some more "batteries included" plugins.

## CQRS Links:
 - [Greg Young: Unshackle Your Domain](http://www.infoq.com/presentations/greg-young-unshackle-qcon08)
 - [Udi Dahan: CQRS](http://www.infoq.com/presentations/Command-Query-Responsibility-Segregation)

## API Docs
[Read the Docs](https://recall.readthedocs.org/en/latest/)

## Todo
 - [x] Add AMQP Event Router
 - [ ] Add Event replay
 - [ ] Add Redis Event Store
 - [ ] Add Memcached Snapshot Store
 - [ ] Tests!

## Tracks
This PHP library is the basis for Recall, but don't let PHP stop you. [Tracks](https://github.com/spiralout/Tracks) is a well thought-out framework used in production every day. Not to mention that spiralout is the guy that introduced me to CQRS.
