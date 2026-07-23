# app/core/locking.py
import time
import uuid

def acquire_lock(redis_client, resource_key: str, timeout_seconds: int = 5, wait_seconds: int = 3):
    """
    Tries to acquire a lock on `resource_key`.
    Returns a unique lock_id if successful, or None if it couldn't get the lock in time.
    """
    lock_key = f"lock:{resource_key}"
    lock_id = str(uuid.uuid4())  # unique value so we only release OUR OWN lock, not someone else's
    
    end_time = time.time() + wait_seconds
    while time.time() < end_time:
        # SET ... NX EX — atomic: only succeeds if the lock doesn't already exist
        acquired = redis_client.set(lock_key, lock_id, nx=True, ex=timeout_seconds)
        if acquired:
            return lock_id
        time.sleep(0.1)  # wait 100ms before trying again
    
    return None  # gave up after wait_seconds — too much contention


def release_lock(redis_client, resource_key: str, lock_id: str):
    """
    Only releases the lock if it's still ours (matches lock_id) —
    prevents accidentally releasing a lock that expired and was re-acquired by someone else.
    """
    lock_key = f"lock:{resource_key}"
    current_value = redis_client.get(lock_key)
    if current_value == lock_id:
        redis_client.delete(lock_key)