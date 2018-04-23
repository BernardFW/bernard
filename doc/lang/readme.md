Language management
===================

Bots deal heavily with natural language, may it be generating it or
understanding it.

As explained in the [Get Started](../get-started/readme.md) part, the
state of the art on NLU is quite limited and doesn't allow to make a
bot that passes the
[Turing test](https://en.wikipedia.org/wiki/Turing_test), not even
closely.

The good news is that the goal if bots is in no way to speak the human
language but rather to provide a quick shortcut to access a specific
service. And in this condition of knowing a very specific context it
becomes possible to have some understanding of what the person says.

On the other hand, in order to reply, you will have to generate
sentences that your user will understand. This is somewhat similar to
what websites have been doing for years, however the "translation"
system in BERNARD is much more flexible that what gettext and others
usually allow in order to create more engaging conversations.

This section is organized as follows:

- [NLU](./nlu.md) (Natural Language Understanding)
- [NLG](./nlg.md) (Natural Language Generation)
