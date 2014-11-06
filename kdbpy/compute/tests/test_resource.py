import pytest

import pandas as pd
import pandas.util.testing as tm
bz = pytest.importorskip('blaze')
from toolz import first
from blaze import Data, by, into, compute
from blaze.compute.core import swap_resources_into_scope
from kdbpy.compute.qtable import issplayed, isstandard


@pytest.fixture
def daily(rstring, kdbpar):
    return Data(rstring + '/start/db::daily', engine=kdbpar)


@pytest.fixture
def nbbo(rstring, kdbpar):
    return Data(rstring + '/start/db::nbbo_t', engine=kdbpar)


def test_resource_doesnt_bork(daily):
    assert repr(daily)


def test_field(daily):
    qresult = daily.price
    expr, daily = swap_resources_into_scope(qresult, {})
    expected = compute(expr, into(pd.DataFrame, first(daily.values())))
    result = into(pd.Series, qresult)
    assert result.name == expected.name
    tm.assert_series_equal(result, expected)


def test_field_name(daily):
    qresult = daily.price
    names = repr(qresult).split('\n')[0].strip().split()
    assert len(names) == 1
    assert names[0] == 'price'


def test_simple_op(daily):
    qresult = daily.price + 1
    result = into(pd.DataFrame, qresult)
    df = into(pd.DataFrame, daily)
    expr, daily = swap_resources_into_scope(qresult, {})
    expected = into(pd.DataFrame(columns=expr.fields), compute(expr, df))
    tm.assert_frame_equal(result, expected)


def test_complex_date_op_repr(daily, kdb):
    sym = bz.Symbol('daily', daily.dshape)
    result = by(sym.date.month,
                cnt=sym.nrows,
                size=sym.size.sum(),
                wprice=(sym.price * sym.size).sum() / sym.price.count())
    assert repr(result)


def test_complex_date_op(daily):
    # q) select cnt: count price, size: sum size, wprice: size wavg price
    #       by date from daily
    qresult = by(daily.date,
                 cnt=daily.price.count(),
                 size=daily.size.sum(),
                 wprice=(daily.size * daily.price).sum() / daily.price.sum())
    assert repr(qresult)
    result = sorted(into(list, into(pd.DataFrame, qresult).reset_index()))
    expr, daily = swap_resources_into_scope(qresult, {})
    expected = sorted(compute(expr, into(list, into(pd.DataFrame,
                                                    first(daily.values())))))
    assert result == expected


def test_complex_nondate_op(daily):
    # q) select cnt: count price, size: sum size, wprice: size wavg price
    #       by sym from daily
    qresult = by(daily.sym,
                 cnt=daily.price.count(),
                 size=daily.size.sum(),
                 wprice=(daily.size * daily.price).sum() / daily.price.sum())
    assert repr(qresult)
    result = sorted(into(list, into(pd.DataFrame, qresult).reset_index()))
    expr, daily = swap_resources_into_scope(qresult, {})
    expected = sorted(compute(expr, into(list, into(pd.DataFrame,
                                                    first(daily.values())))))
    assert result == expected


def test_issplayed(nbbo):
    assert issplayed(nbbo)


def test_isstandard(daily):
    assert isstandard(daily)


def test_by_mean(daily):
    qresult = by(daily.sym, daily.price.mean())
    expr, daily = swap_resources_into_scope(qresult, {})
    expected = compute(expr, into(pd.DataFrame, first(daily.values())))
    expected = expected.set_index('sym')
    result = into(pd.DataFrame, qresult)
    tm.assert_frame_equal(result, expected)