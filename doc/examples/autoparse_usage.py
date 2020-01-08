import dataclasses

from validobj.errors import WrongFieldError

from autoparse_decorator import autoparse

user_funds = {'Alice': 300, 'Bob': 150, 'Eve': 33}


@dataclasses.dataclass
class Transfer:
    origin: str
    destination: str
    quantity: int


@autoparse
def check_transfer(tr: Transfer):
    if tr.origin not in user_funds:
        raise WrongFieldError("Originating user does not exist", wrong_field='origin')
    if tr.destination not in user_funds:
        raise WrongFieldError(
            "Destination user does not exist", wrong_field='destination'
        )
    if tr.quantity > user_funds[tr.origin]:
        raise WrongFieldError("Insufficient funds", wrong_field='quantity')
    return tr
