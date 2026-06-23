value("LS"). value("L"). value("VL"). value("AC"). value("C").

less_than("LS","L"). less_than("L","VL"). less_than("VL","AC"). less_than("AC","C").
less_than(X,Z) :- less_than(X,Y), less_than(Y,Z).

% ---------- 1. Generate Assignments ----------

{ credibility(N, V) : value(V) } <= 1 :- node(N), not user_assigned(N).
{ relevance(From, To, Type, V) : value(V) } <= 1 :- unknown_edge(From, To, Type).


% ---------- 2. Inference Calculations ----------

final_credibility(N, V) :- user_assigned(N), credibility(N, V).
final_credibility(N, V) :- not user_assigned(N), credibility(N, V).

final_relevance(F, T, Type, V) :- edge(F, T, Type, V). % Known edges
final_relevance(F, T, Type, V) :- relevance(F, T, Type, V). % Assigned to unknown edges

inference_strength(From, To, Type, Relevance) :-
    final_relevance(From, To, Type, Relevance),
    final_credibility(From, Cred),
    less_than(Relevance, Cred).

inference_strength(From, To, Type, Cred) :-
    final_relevance(From, To, Type, Relevance),
    final_credibility(From, Cred),
    not less_than(Relevance, Cred), 
    not less_than(Cred, Relevance). % Handles Cred = Relevance

inference_strength(From, To, Type, Cred) :-
    final_relevance(From, To, Type, Relevance),
    final_credibility(From, Cred),
    less_than(Cred, Relevance).

stronger(To, Type, S) :-
    inference_strength(_, To, Type, S),
    inference_strength(_, To, Type, T),
    less_than(S, T).

combined_strength(To, Type, S) :-
    inference_strength(_, To, Type, S),
    not stronger(To, Type, S).

combined_strength(To, support, "LS") :-
    node(To),
    not edge(_, To, support, _),
    not unknown_edge(_, To, support).

combined_strength(To, attack, "LS") :-
    node(To),
    not edge(_, To, attack, _),
    not unknown_edge(_, To, attack).

% g(F_sup, F_att)
function("LS","LS","LS"). function("LS","L","LS"). function("LS","VL","LS"). function("LS","AC","LS"). function("LS","C","LS").
function("L","LS","L").   function("L","L","LS").  function("L","VL","LS").  function("L","AC","LS").  function("L","C","LS").
function("VL","LS","VL"). function("VL","L","L").  function("VL","VL","LS"). function("VL","AC","LS"). function("VL","C","LS").
function("AC","LS","AC"). function("AC","L","VL"). function("AC","VL","L").  function("AC","AC","LS"). function("AC","C","LS").
function("C","LS","C").   function("C","L","AC").  function("C","VL","VL").  function("C","AC","L").   function("C","C","LS").

inferred_credibility(N, F) :-
    node(N),
    not leaf_node(N),
    combined_strength(N, support, S),
    combined_strength(N, attack, A),
    function(S, A, F).


% ---------- 3. Consistency Check ----------
leaf_node(N) :-
    node(N),
    not edge(_, N, support, _),
    not unknown_edge(_, N, support),
    not edge(_, N, attack, _),
    not unknown_edge(_, N, attack).

inconsistency(N, C, F) :-
    node(N),
    not leaf_node(N),
    final_credibility(N, C),
    inferred_credibility(N, F),
    C != F.

inconsistency(N, F) :-
    node(N),
    not leaf_node(N),
    not final_credibility(N, _),
    inferred_credibility(N, F).

:- inconsistency(_, _, _).
:- inconsistency(_, _).


% ---------- 4. Output ----------
consistent_argument_status(N, V) :-
    node(N),
    not leaf_node(N),
    final_credibility(N, V).

consistent_argument_status(N, "consistent_no_value") :-
    node(N),
    not leaf_node(N),
    not final_credibility(N, _),
    not inferred_credibility(N, _). % This ensures it's the v_init=⊥, v_inf=⊥ case


leaf_argument_status(N, V) :-
    leaf_node(N),
    final_credibility(N, V).

leaf_argument_status(N, "no_value_assigned") :-
    leaf_node(N),
    not final_credibility(N, _).

#show consistent_argument_status/2.

#show leaf_argument_status/2.
