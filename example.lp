#include "rule.lp".

node(1..4).

user_assigned(2). credibility(2, "L"). 
user_assigned(3). credibility(3, "C").

edge(3, 4, support, "C").

unknown_edge(1, 2, support).
unknown_edge(4, 1, attack).
unknown_edge(2, 4, attack).
