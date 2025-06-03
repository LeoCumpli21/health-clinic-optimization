"""This module provides functions for manipulating a customer priority queue,
including calculating optimal positions for priority customers and updating the queue
based on service times and priority thresholds.
"""

from datetime import datetime
from typing import List, Tuple, Set

from src.entities.customer import Customer
from src.interfaces.priority_queue import (
    PriorityQueue,
)
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
    max_jumps_p: int,
    jumps_limit: int,
) -> int:
    """Calculates how many positions forward a priority customer can be moved.

    This function determines the number of positions a given priority customer
    (`customer`, who is at `queue_n_times[0]`) can move ahead in the queue.
    It iterates through customers preceding the priority customer.

    A skip over a non-priority (NP) customer (`np_customer_to_skip`) is considered if:
    1. `np_customer_to_skip` has been jumped fewer times than `jumps_limit`.
    2. One of the following conditions for `np_customer_to_skip`'s waiting time is met:
        a. Its new estimated waiting time (if skipped by `customer`) does not
           exceed `non_p_threshold`.
        b. Its new estimated waiting time *does* exceed `non_p_threshold`,
           but `customer` has unused "special jumps" available from their
           `max_jumps_p` budget for this evaluation.

    The process of accumulating skips stops if:
    - A preceding customer is also a priority type.
    - An NP customer cannot be skipped due to their `jumps` count reaching `jumps_limit`.
    - An NP customer cannot be skipped because their `non_p_threshold` would be
      exceeded, AND the priority `customer` has no `max_jumps_p` budget remaining.
    - The priority `customer`'s own estimated waiting time falls below `p_threshold`.

    Args:
        queue_n_times: A list of (Customer, float) tuples. This list
            represents the segment of the queue from the priority customer
            (at index 0) up to the front, in reversed order. The float value
            is the customer's current estimated waiting time.
            `queue_n_times[0]` is the priority customer being evaluated.
        customer: The priority `Customer` object whose potential move is being
            evaluated. This should be identical to `queue_n_times[0][0]`.
        p_threshold: The target estimated waiting time for the `customer`.
        non_p_threshold: The maximum permissible estimated waiting time for
            any NP customer that `customer` skips (unless overridden by `max_jumps_p`).
        priority_tickets: A set of ticket type strings that identify
            priority customers.
        service_times_repo: A `Repository` instance used to retrieve
            estimated service times.
        max_jumps_p: The maximum number of times the evaluating `customer` can
            force a jump over an NP customer even if `non_p_threshold` is
            exceeded for that NP customer, during this specific evaluation call.
        jumps_limit: The absolute maximum number of times any NP customer
            can be jumped over in their lifetime in the queue.

    Returns:
        An integer representing the number of positions the `customer` can be
        moved forward (i.e., number of NP customers successfully skipped).
    """
    new_pos = 0
    new_estimated_waiting_time_p = queue_n_times[0][1]

    p_jumps_used_this_call = 0

    for ix in range(len(queue_n_times)):
        if ix > 0:
            customer_to_skip = queue_n_times[ix][0]
            original_wait_time_for_customer_to_skip = queue_n_times[ix][1]

            if customer_to_skip.ticket_type in priority_tickets:
                break

            if customer_to_skip.jumps >= jumps_limit:
                break

            new_estimated_waiting_time_non_p = (
                original_wait_time_for_customer_to_skip
                + get_estimated_service_time(customer, service_times_repo)
            )

            can_skip_this_np = False
            made_a_special_jump_for_this_np = False

            if new_estimated_waiting_time_non_p <= non_p_threshold:
                can_skip_this_np = True
            elif p_jumps_used_this_call < max_jumps_p:
                can_skip_this_np = True
                made_a_special_jump_for_this_np = True
            else:
                break

            if can_skip_this_np:
                if made_a_special_jump_for_this_np:
                    p_jumps_used_this_call += 1

                new_estimated_waiting_time_p = (
                    new_estimated_waiting_time_p
                    - get_estimated_service_time(customer_to_skip, service_times_repo)
                )

                queue_n_times[ix] = (customer_to_skip, new_estimated_waiting_time_non_p)
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
    max_jumps_p: int,
    jumps_limit: int,
    debug: bool = False,
) -> PriorityQueue:
    """Optimizes the customer queue by iteratively moving priority customers forward.

    This function evaluates priority (P) customers whose total estimated waiting
    time exceeds `p_threshold`. It attempts to move them forward by skipping
    non-priority (NP) customers.

    A P customer can skip an NP customer if:
    - The NP customer has been jumped fewer than `jumps_limit` times.
    - Skipping them doesn't make the NP customer's wait time exceed `non_p_threshold`,
      OR the P customer uses one of their `max_jumps_p` allowances for the current
      evaluation round (as determined by `calculate_customer_new_position`).

    If a P customer is moved, the `jumps` attribute of the NP customers they
    skipped over is incremented.

    The process is iterative (stabilization loop): after any move, estimated
    waiting times are recalculated, and the queue is re-evaluated from the
    beginning until no more moves are made in a full pass.

    Args:
        queue: The live priority queue object.
        service_times_repo: Repository for estimated service times.
        service_points: Number of available service points.
        priority_tickets: Set of ticket types identifying priority customers.
        p_threshold: Target maximum total waiting time for a P customer.
        non_p_threshold: Maximum permissible total waiting time for an NP
            customer skipped by a P customer (can be overridden by `max_jumps_p`).
        current_time: Current time for calculating total estimated wait times.
        max_jumps_p: The budget a P customer has in a single evaluation call
            to `calculate_customer_new_position` to make "threshold-breaking"
            jumps.
        jumps_limit: The maximum number of times an NP customer can be jumped.
        debug: Whether to print detailed debugging information.

    Returns:
        The modified queue object with optimized customer positions.
    """
    optimization_pass = 0
    total_moves = 0

    while True:
        optimization_pass += 1
        made_change_in_pass = False

        if debug:
            print(f"\n--- Optimization Pass {optimization_pass} ---")

        estimated_waiting_times = estimate_total_times_in_line(
            service_points, queue, service_times_repo, current_time
        )

        customers_at_pass_start = []
        for i, customer_obj in enumerate(queue):
            customers_at_pass_start.append(
                {"customer": customer_obj, "original_est_idx": i}
            )

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
                            "jumps": customer_obj.jumps,
                            "exceeds_threshold": wait_time > p_threshold,
                        }
                    )

            print(f"Priority customers in queue: {len(priority_customers_info)}")
            for info in priority_customers_info:
                status = "⚠️ ABOVE THRESHOLD" if info["exceeds_threshold"] else "✅ OK"
                print(
                    f"  Pos {info['position']}: Customer {info['customer_id']} (Jumps: {info['jumps']}) - {info['wait_time']:.1f} min ({status})"
                )

        for customer_info in customers_at_pass_start:
            current_customer = customer_info["customer"]
            original_est_idx = customer_info["original_est_idx"]
            current_actual_idx = original_est_idx

            if current_customer.ticket_type in priority_tickets:
                customer_estimated_wait = estimated_waiting_times[original_est_idx][1]

                # if customer_estimated_wait > p_threshold:
                if debug:
                    print(
                        f"\n🔍 Evaluating Customer {current_customer.customer_id} (P) at pos {current_actual_idx + 1} (Jumps: {current_customer.jumps})"
                    )
                    print(
                        f"   Current wait time: {customer_estimated_wait:.1f} min (exceeds {p_threshold:.1f} min threshold)"
                    )
                    print(
                        f"   P's special jump budget for this eval: {max_jumps_p}, NP jump limit overall: {jumps_limit}"
                    )

                relevant_times_slice = estimated_waiting_times[: original_est_idx + 1][
                    ::-1
                ]

                num_positions_to_skip = calculate_customer_new_position(
                    relevant_times_slice,
                    current_customer,
                    p_threshold,
                    non_p_threshold,
                    priority_tickets,
                    service_times_repo,
                    max_jumps_p,
                    jumps_limit,
                )

                if num_positions_to_skip > 0:
                    new_target_index = current_actual_idx - num_positions_to_skip
                    if new_target_index < 0:
                        new_target_index = 0

                    if new_target_index != current_actual_idx:
                        if debug:
                            print(
                                f"   ✅ MOVING Customer {current_customer.customer_id}: position {current_actual_idx + 1} → {new_target_index + 1} (skipping {num_positions_to_skip} customers)"
                            )

                        customers_before_move = list(queue)
                        skipped_customers_details_debug = []
                        for i in range(num_positions_to_skip):
                            skipped_customer_original_idx = new_target_index + i
                            if skipped_customer_original_idx < current_actual_idx:
                                skipped_customer = customers_before_move[
                                    skipped_customer_original_idx
                                ]
                                if skipped_customer.ticket_type not in priority_tickets:
                                    skipped_customer.update_jumps()
                                    if debug:
                                        skipped_customers_details_debug.append(
                                            f"ID {skipped_customer.customer_id} (NP) now has {skipped_customer.jumps} jumps (limit {jumps_limit})"
                                        )
                                elif debug:
                                    print(
                                        f"   ⚠️ WARNING: Attempted to update jumps for a P customer (ID {skipped_customer.customer_id}) in skip path."
                                    )
                            else:
                                if debug:
                                    print(
                                        f"   ⚠️ WARNING: Skipped customer index logic error. Idx: {skipped_customer_original_idx}, P_orig_idx: {current_actual_idx}"
                                    )

                        if debug and skipped_customers_details_debug:
                            print(
                                f"     Updated jumps for: {'; '.join(skipped_customers_details_debug)}"
                            )
                        elif debug and num_positions_to_skip > 0:
                            print(
                                f"     No NP customers recorded for jump updates, despite num_positions_to_skip={num_positions_to_skip}."
                            )

                        queue.update_priority(current_customer, new_target_index)
                        made_change_in_pass = True
                        total_moves += 1
                        break
                    else:
                        if debug:
                            print(
                                f"   ⏸️ No move needed for Customer {current_customer.customer_id} - calculated position same as current."
                            )
                else:
                    if debug:
                        print(
                            f"   ❌ Cannot move Customer {current_customer.customer_id} - no valid positions (blocked or no benefit)."
                        )
                # elif debug:
                #    print(
                #        f"   ✅ Customer {current_customer.customer_id} (P) at pos {current_actual_idx + 1}: {customer_estimated_wait:.1f} min (OK)"
                #    )

        if not made_change_in_pass:
            if debug:
                print(f"\n--- Pass {optimization_pass} complete: No changes made ---")
            break

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
