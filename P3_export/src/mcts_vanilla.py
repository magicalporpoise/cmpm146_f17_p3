
from mcts_node import MCTSNode
import random
from math import sqrt, log
from p3_t3 import Board

num_nodes = 500
exploit_faction = 1
explore_faction = 2
all_visits = 1

def traverse_nodes(node, state, board, identity):
    """ Traverses the tree until the end criterion are met.

    Args:
        node:       A tree node from which the search is traversing.
        state:      The state of the game.
        identity:   The bot's identity, either 'red' or 'blue'.

    Returns:        A node from which the next stage of the search can proceed.
    """
    #print("-in SEL-", end="")
    # traverse from the node root
    # any children?
    best_node = node
    best_action = None
    leaf_node = best_node
    # look at children's UCT scores
    # pick best OR pick random untried
    best_score = uct(best_node.wins, best_node.visits)
    while(len(best_node.child_nodes) != 0):
        parent_node = best_node
        for action, child in best_node.child_nodes.items():
            current_score = uct(child.wins, child.visits)
            if current_score > best_score:
                best_score = current_score
                best_node = child
                #best_action = child.parent_action
        if best_node == parent_node:
            break
    
    # return best node
    return best_node#, best_action
    # Hint: return leaf_node

def uct(wins, visits):
    exploit = exploit_faction*(wins / (visits))
    explore = explore_faction*sqrt(log(all_visits)/(visits))
    score = exploit + explore
    return score
                                       
def expand_leaf(node, state, board, cur_player):
    """ Adds a new leaf to the tree by creating a new child node for the given node.

    Args:
        node:   The node for which a child will be added.
        state: state of the game

    Returns:    The added child node.

    """
    
    # Now pick which to potentially expand
    if node.parent != None and len(node.parent.untried_actions)>0:
        moves = node.parent.untried_actions
        pick_rando = True
        if len(moves) < 9:
            my_boxes = len([v for v in board.owned_boxes(state).values() if v == cur_player])
            for maybe_move in moves:
                R, C, r, c = maybe_move
                if r == 0 and c == 0:
                    action_taken = maybe_move
                    pick_rando=False
                    break
                else:
                    potential_state = board.next_state(state, maybe_move)
                    if len([v for v in board.owned_boxes(potential_state).values() if v == cur_player]) > my_boxes:
                        action_taken = maybe_move
                        pick_rando=False
                        break      
        # randomly pick an untried action
        if pick_rando:
           action_taken = random.choice(moves)
           moves.remove(action_taken)
    else:
        # randomly pick a legal action
        action_taken = random.choice(board.legal_actions(state))

    #updtae state
    state = board.next_state(state, action_taken)
        
    # get legal moves
    la = board.legal_actions(state)
    
    # initialize new node
    new_node = MCTSNode(node, action_taken, la)
    #add to nodes children
    node.child_nodes[action_taken] = new_node
    # return new node
    return new_node
    # Hint: return new_node


def rollout(board, state, identity):
    """ Given the state of the game, the rollout plays out the remainder randomly.

    Args:
        board: reference to the board
        state:  The state of the game.
        identity: who this bot is (1 or 2)

    simulate the game and returna  value based on if won or lsot
    """
    #print("-in ROLL-", end="")
    # random sim till end of game
    me = board.current_player(state)
    rollout_state = state
    # Random choice, unless it allows me to capture a box
    while not board.is_ended(rollout_state):
        cur_player = board.current_player(rollout_state)
        moves = board.legal_actions(rollout_state)
        rollout_move = random.choice(moves)
        rollout_state = board.next_state(rollout_state, rollout_move)

    #neg for loss, neutral for tie, pos for win
    # Define a helper function to calculate the difference between the bot's score and the opponent's.
    def outcome(owned_boxes, game_points):
        i = identity
        e = identity%2 +1
        my_score = game_points[i]
        not_score = game_points[e]
        #my_score += len([v for v in owned_boxes.values() if v == i])
        #not_score += len([v for v in owned_boxes.values() if v == e])
        return my_score if my_score > not_score else not_score


    sim_value = outcome(board.owned_boxes(rollout_state), board.points_values(rollout_state))

    return sim_value

def backpropagate(node, won):
    """ Navigates the tree from a leaf node to the root, updating the win and visit count of each node along the path.

    Args:
        node:   A leaf node.
        won:    An indicator of whether the bot won or lost the game.

        return the number of nodes visited
    """
    #print("-in BP-", end="")
    av = 0
    # Travel down the tree of inheritence
    while(node.parent != None):
        av+=1
        node.visits+=1
        node.wins += won
        node = node.parent
    #av+=1
    #node.visits+=1
    #node.wins += won

    return av

def think(board, state):
    """ Performs MCTS by sampling games and calling the appropriate functions to construct the game tree.

    Args:
        board:  The game setup.
        state:  The state of the game.

    Returns:    The action to be taken.

    """
    print("HELLO, I AM THINKING ABOUT MY NEXT MOVE\n")
    identity_of_bot = board.current_player(state)
    root_node = MCTSNode(parent=None, parent_action=None, action_list=board.legal_actions(state))
    all_visits = 0
    for step in range(num_nodes):
        # Copy the game for sampling a playthrough
        sampled_game = state

        # Start at root
        node = root_node

        # Do MCTS - This is all you!
        # Selection
        leaf_node = traverse_nodes(node, sampled_game, board, identity_of_bot)
        #Expansion
        expanded_node = expand_leaf(leaf_node, sampled_game, board, identity_of_bot)
        # Rollout
        roll_score = rollout(board, sampled_game, identity_of_bot)
        # Propogate
        all_visits += backpropagate(expanded_node, roll_score)

    # Return an action, typically the most frequently used action (from the root) or the action with the best
    # estimated win rate.
    print(root_node.tree_to_string())
    best_action = None
    best_score = -100000
    action_child_list = root_node.child_nodes.items()
    for action, child in action_child_list:
        #print("CHILD: " + str(child) + "\n")
        current_score = uct(child.wins, child.visits)
        if current_score > best_score:
            best_score = current_score
            best_action = action
    print("I think the best play is..." + str(best_action) + "score= " + str(best_score))
    return best_action
