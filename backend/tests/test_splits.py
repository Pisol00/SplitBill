from decimal import Decimal

from app.services.splits import allocate_equal, check_exact


def test_equal_split_of_100_among_three_gives_33_34_33_33_33_33():
    shares = allocate_equal(Decimal("100.00"), ["alice", "bob", "carol"])

    assert shares == [
        ("alice", Decimal("33.34")),
        ("bob", Decimal("33.33")),
        ("carol", Decimal("33.33")),
    ]


def test_equal_split_of_brief_example_1000_among_three():
    shares = allocate_equal(Decimal("1000.00"), ["alice", "bob", "carol"])

    assert shares == [
        ("alice", Decimal("333.34")),
        ("bob", Decimal("333.33")),
        ("carol", Decimal("333.33")),
    ]


def test_equal_split_gives_remainder_satang_in_the_order_listed():
    shares = allocate_equal(Decimal("100.00"), ["carol", "alice", "bob"])

    assert shares == [
        ("carol", Decimal("33.34")),
        ("alice", Decimal("33.33")),
        ("bob", Decimal("33.33")),
    ]


def test_equal_split_gives_one_satang_each_to_the_first_members_for_two_satang():
    shares = allocate_equal(Decimal("100.01"), ["alice", "bob", "carol"])

    assert shares == [
        ("alice", Decimal("33.34")),
        ("bob", Decimal("33.34")),
        ("carol", Decimal("33.33")),
    ]


def test_equal_split_without_remainder_gives_identical_shares():
    shares = allocate_equal(Decimal("90.00"), ["alice", "bob", "carol"])

    assert shares == [
        ("alice", Decimal("30.00")),
        ("bob", Decimal("30.00")),
        ("carol", Decimal("30.00")),
    ]


def test_equal_split_of_one_satang_among_three_gives_zero_shares():
    shares = allocate_equal(Decimal("0.01"), ["alice", "bob", "carol"])

    assert shares == [
        ("alice", Decimal("0.01")),
        ("bob", Decimal("0.00")),
        ("carol", Decimal("0.00")),
    ]


def test_equal_split_with_one_member_gives_the_full_amount():
    assert allocate_equal(Decimal("123.45"), ["dan"]) == [("dan", Decimal("123.45"))]


def test_equal_split_shares_always_sum_to_the_amount():
    for amount in ["0.01", "0.02", "1.00", "10.00", "99.99", "100.00", "9999999999.99"]:
        for member_count in range(1, 8):
            members = [f"member{i}" for i in range(member_count)]

            shares = allocate_equal(Decimal(amount), members)

            assert sum(share for _, share in shares) == Decimal(amount)
            assert all(share.as_tuple().exponent == -2 for _, share in shares)


def test_exact_split_not_summing_to_the_amount_is_rejected():
    shares = [("alice", Decimal("500.00")), ("bob", Decimal("300.00"))]

    assert check_exact(Decimal("1000.00"), shares) is None


def test_exact_split_summing_to_the_amount_is_accepted_in_the_given_order():
    shares = [
        ("carol", Decimal("200.00")),
        ("alice", Decimal("500.00")),
        ("bob", Decimal("300.00")),
    ]

    assert check_exact(Decimal("1000.00"), shares) == shares


def test_exact_split_off_by_one_satang_is_rejected():
    shares = [("alice", Decimal("500.00")), ("bob", Decimal("499.99"))]

    assert check_exact(Decimal("1000.00"), shares) is None
