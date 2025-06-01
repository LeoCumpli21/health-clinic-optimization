"""This module provides functions for manipulating a customer priority queue,
including calculating optimal positions for priority customers and updating the queue
based on service times and priority thresholds.
"""

from datetime import datetime
from typing import List, Tuple, Set

from src.entities.customer import Customer
from src.interfaces.priority_queue import PriorityQueue
from src.interfaces.repository import Repository
from src.services.estimate_time_left import (
    estimate_total_times_in_line,
    get_estimated_service_time,
)


def calculate_customer_new_position(
    queue_n_times: List[Tuple[Customer, float]],
    customer: Customer,
    p_threshold: float,
    non_p_threshold: float,
    priority_tickets: Set[str],
    service_times_repo: Repository,
) -> int:
    """Calculates how many positions forward a priority customer can be moved.

    This function determines the number of positions a given priority customer
    can be moved ahead in the queue. It iterates through the customers
    preceding the priority customer (who is at `queue_n_times[0]`).

    For each non-priority customer that the priority customer might skip:
    1.  The estimated waiting time of the non-priority customer (if skipped)
        must not exceed `non_p_threshold`.
    2.  The priority customer's own estimated waiting time is recalculated.

    The process of accumulating skips (and thus moving the priority customer
    forward) stops if any of the following conditions are met:
    -   A preceding customer is also of a priority ticket type (priority
        customers do not skip other priority customers using this logic).
    -   Skipping a non-priority customer would cause that non-priority
        customer's estimated waiting time to exceed `non_p_threshold`.
    -   The priority customer's own estimated waiting time falls below
        `p_threshold` as a result of the moves.

    Args:
        queue_n_times: A list of (Customer, float) tuples. This list
            represents the segment of the queue from the priority customer
            (at index 0) up to the front, in reversed order. The float value
            is the customer's current estimated waiting time.
            `queue_n_times[0]` is the priority customer being evaluated.
        customer: The priority `Customer` object whose potential move is being
            evaluated. This should be identical to `queue_n_times[0][0]`.
        p_threshold: The target estimated waiting time for the `customer`.
            The function aims to move the customer forward until their
            estimated waiting time is below this value.
        non_p_threshold: The maximum permissible estimated waiting time for
            any non-priority customer that `customer` skips over.
        priority_tickets: A set of ticket type strings that identify
            priority customers.
        service_times_repo: A `Repository` instance used to retrieve
            estimated service times for customers.

    Returns:
        An integer representing the number of positions the `customer` can be
        moved forward in the queue. This corresponds to the count of
        non-priority customers they can successfully skip while satisfying
        the defined threshold conditions. Returns 0 if no move is possible
        or beneficial according to the criteria.
    """
    new_pos = 0
    new_estimated_waiting_time_p = queue_n_times[0][1]
    new_estimated_waiting_time_non_p = 0
    for ix in range(len(queue_n_times)):
        if ix > 0:
            # check if current customer is a priority ticket
            if queue_n_times[ix][0].ticket_type in priority_tickets:
                break
            # check what happens if p customer is moved to the current position
            # how it affects the waiting time of the non-p customers
            new_estimated_waiting_time_non_p = queue_n_times[ix][
                1
            ] + get_estimated_service_time(customer, service_times_repo)
            if new_estimated_waiting_time_non_p > non_p_threshold:
                break
            # how it affects the waiting time of the customer
            new_estimated_waiting_time_p = (
                new_estimated_waiting_time_p
                - get_estimated_service_time(queue_n_times[ix][0], service_times_repo)
            )
            queue_n_times[ix] = (queue_n_times[ix][0], new_estimated_waiting_time_non_p)

            new_pos = ix
            if new_estimated_waiting_time_p < p_threshold:
                break

    return new_pos


def update_queue_improved(
    queue: PriorityQueue,
    service_times_repo: Repository,
    service_points: int,
    priority_tickets: Set[str],
    p_threshold: float,
    non_p_threshold: float,
    current_time: datetime,
    debug: bool = False,
) -> PriorityQueue:
    """Optimizes the customer queue by iteratively moving priority customers forward.

    This function repeatedly evaluates the queue and attempts to move priority
    customers to better positions. A move is considered if a priority customer's
    total estimated waiting time (time already waited + future estimated wait)
    exceeds `p_threshold`. The customer is moved forward by skipping non-priority
    customers, as long as the skipped non-priority customers' new total estimated
    waiting times do not exceed `non_p_threshold`, and the priority customer's
    own total waiting time does not drop below `p_threshold` too soon (as per
    `calculate_customer_new_position` logic).

    The process is iterative (stabilization loop): after each successful move of a
    priority customer, the total estimated waiting times for all customers are
    recalculated using the provided `current_time`, and the entire queue is
    re-evaluated from the beginning. This ensures that decisions are based on the
    most current state of the queue and total accumulated wait times.
    The loop continues until a full pass over all customers in the queue results
    in no changes, indicating a stabilized state.

    Args:
        queue (PriorityQueue): The live priority queue object to be modified.
        service_times_repo (Repository): Repository to fetch estimated service times.
        service_points (int): The number of available service points.
        priority_tickets (Set[str]): A set of ticket type strings that identify
            priority customers.
        p_threshold (float): The target maximum total estimated waiting time for a
            priority customer. If a priority customer's total wait time is above this,
            an attempt is made to move them forward.
        non_p_threshold (float): The maximum permissible total estimated waiting time for
            any non-priority customer that a priority customer skips over.
        current_time (datetime): The current time, used for calculating total
            estimated waiting times (including time already spent in queue).
        debug (bool): Whether to print detailed debugging information.

    Returns:
        PriorityQueue: The modified queue object with optimized customer positions.
    """
    optimization_pass = 0
    total_moves = 0

    if debug:
        print(f"\n=== QUEUE OPTIMIZATION START ===")
        print(
            f"P-threshold: {p_threshold:.1f} min, NP-threshold: {non_p_threshold:.1f} min"
        )
        _print_queue_state(
            queue, estimated_waiting_times=None, title="Initial Queue State"
        )

    while True:  # Stabilization loop
        optimization_pass += 1
        made_change_in_pass = False

        if debug:
            print(f"\n--- Optimization Pass {optimization_pass} ---")

        # Recalculate estimates at the start of each pass using the current queue state
        estimated_waiting_times = estimate_total_times_in_line(
            service_points, queue, service_times_repo, current_time  # Pass current_time
        )

        customers_at_pass_start = []
        for i, customer_obj in enumerate(queue):  # queue is live
            customers_at_pass_start.append(
                {"customer": customer_obj, "original_est_idx": i}
            )

        # Count priority customers and their positions for debugging
        if debug:
            priority_customers_info = []
            for i, customer_obj in enumerate(queue):
                if customer_obj.ticket_type in priority_tickets:
                    wait_time = estimated_waiting_times[i][1]
                    priority_customers_info.append(
                        {
                            "position": i + 1,
                            "customer_id": customer_obj.customer_id,
                            "wait_time": wait_time,
                            "exceeds_threshold": wait_time > p_threshold,
                        }
                    )

            print(f"Priority customers in queue: {len(priority_customers_info)}")
            for info in priority_customers_info:
                status = "⚠️ ABOVE THRESHOLD" if info["exceeds_threshold"] else "✅ OK"
                print(
                    f"  Pos {info['position']}: Customer {info['customer_id']} - {info['wait_time']:.1f} min ({status})"
                )

        for customer_info in customers_at_pass_start:
            current_customer = customer_info["customer"]
            original_est_idx = customer_info["original_est_idx"]

            # Because the stabilization loop breaks and restarts after any change,
            # the 'queue' object and 'estimated_waiting_times' are consistent
            # with 'customers_at_pass_start' for the customer being evaluated.
            # Thus, current_customer's index in the (unmodified for this iteration)
            # queue is its original_est_idx from the start of this pass.
            current_actual_idx = original_est_idx

            if current_customer.ticket_type in priority_tickets:
                # Use the estimated waiting time from the start of this pass
                customer_estimated_wait = estimated_waiting_times[original_est_idx][1]

                if customer_estimated_wait > p_threshold:
                    if debug:
                        print(
                            f"\n🔍 Evaluating Customer {current_customer.customer_id} (P) at position {current_actual_idx + 1}"
                        )
                        print(
                            f"   Current wait time: {customer_estimated_wait:.1f} min (exceeds {p_threshold:.1f} min threshold)"
                        )

                    # The slice for calculate_customer_new_position must also use `estimated_waiting_times`
                    # from the start of this pass, up to the customer's original position in that list.
                    relevant_times_slice = estimated_waiting_times[
                        : original_est_idx + 1
                    ][::-1]

                    num_positions_to_skip = calculate_customer_new_position(
                        relevant_times_slice,
                        current_customer,
                        p_threshold,
                        non_p_threshold,
                        priority_tickets,
                        service_times_repo,
                    )

                    if num_positions_to_skip > 0:
                        new_target_index = current_actual_idx - num_positions_to_skip
                        if new_target_index < 0:
                            new_target_index = 0  # Ensure not negative

                        # Check if the calculated new position is actually different
                        # This check is important because calculate_customer_new_position might return
                        # a skip count that results in the same index if already at/near front.
                        if new_target_index != current_actual_idx:
                            if debug:
                                print(
                                    f"   ✅ MOVING Customer {current_customer.customer_id}: position {current_actual_idx + 1} → {new_target_index + 1} (skipping {num_positions_to_skip} customers)"
                                )

                            queue.update_priority(current_customer, new_target_index)
                            made_change_in_pass = True
                            total_moves += 1

                            # Critical: A change was made. Break from this inner loop
                            # to restart the while loop (re-calculate estimates, etc.)
                            break
                        else:
                            if debug:
                                print(
                                    f"   ⏸️ No move needed - calculated position same as current"
                                )
                    else:
                        if debug:
                            print(
                                f"   ❌ Cannot move - no valid positions found (blocked by other P customers or thresholds)"
                            )
                elif debug:
                    print(
                        f"   ✅ Customer {current_customer.customer_id} (P) at position {current_actual_idx + 1}: {customer_estimated_wait:.1f} min (under threshold)"
                    )

        if not made_change_in_pass:
            if debug:
                print(f"\n--- Pass {optimization_pass} complete: No changes made ---")
            break  # Exit stabilization loop if a full pass made no changes
        # If made_change_in_pass is true, the inner loop was broken,
        # and the while loop will restart, re-calculating estimates.

    if debug:
        print(f"\n=== QUEUE OPTIMIZATION COMPLETE ===")
        print(f"Total optimization passes: {optimization_pass}")
        print(f"Total customer moves: {total_moves}")

        # Show final queue state
        final_estimated_times = estimate_total_times_in_line(
            service_points, queue, service_times_repo, current_time
        )
        _print_queue_state(queue, final_estimated_times, title="Final Queue State")

    return queue


def _print_queue_state(
    queue: PriorityQueue, estimated_waiting_times=None, title="Queue State"
):
    """Helper function to print the current state of the queue."""
    print(f"\n{title}:")
    print("Pos | Customer ID | Type | Wait Time")
    print("----|-------------|------|----------")

    for i, customer in enumerate(queue):
        wait_time_str = "N/A"
        if estimated_waiting_times:
            wait_time_str = f"{estimated_waiting_times[i][1]:.1f} min"

        ticket_type = customer.ticket_type
        print(
            f"{i+1:3d} | {customer.customer_id:11d} | {ticket_type:4s} | {wait_time_str}"
        )

    print(f"Total customers: {len(list(queue))}")
