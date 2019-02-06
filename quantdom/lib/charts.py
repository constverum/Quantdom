"""Chart."""

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui

from .base import Quotes
from .const import ChartType
from .portfolio import Order, Portfolio
from .utils import fromtimestamp, timeit

__all__ = ('QuotesChart', 'EquityChart')


pg.setConfigOption('background', 'w')
CHART_MARGINS = (0, 0, 20, 5)


class SampleLegendItem(pg.graphicsItems.LegendItem.ItemSample):
    def paint(self, p, *args):
        p.setRenderHint(p.Antialiasing)
        if isinstance(self.item, tuple):
            positive = self.item[0].opts
            negative = self.item[1].opts
            p.setPen(pg.mkPen(positive['pen']))
            p.setBrush(pg.mkBrush(positive['brush']))
            p.drawPolygon(
                QtGui.QPolygonF(
                    [
                        QtCore.QPointF(0, 0),
                        QtCore.QPointF(18, 0),
                        QtCore.QPointF(18, 18),
                    ]
                )
            )
            p.setPen(pg.mkPen(negative['pen']))
            p.setBrush(pg.mkBrush(negative['brush']))
            p.drawPolygon(
                QtGui.QPolygonF(
                    [
                        QtCore.QPointF(0, 0),
                        QtCore.QPointF(0, 18),
                        QtCore.QPointF(18, 18),
                    ]
                )
            )
        else:
            opts = self.item.opts
            p.setPen(pg.mkPen(opts['pen']))
            p.drawRect(0, 10, 18, 0.5)


class PriceAxis(pg.AxisItem):
    def __init__(self):
        super().__init__(orientation='right')
        self.style.update({'textFillLimits': [(0, 0.8)]})

    def tickStrings(self, vals, scale, spacing):
        digts = max(0, np.ceil(-np.log10(spacing * scale)))
        return [
            ('{:<8,.%df}' % digts).format(v).replace(',', ' ') for v in vals
        ]


class DateAxis(pg.AxisItem):
    tick_tpl = {'D1': '%d %b\n%Y'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quotes_count = len(Quotes) - 1

    def tickStrings(self, values, scale, spacing):
        s_period = 'D1'
        strings = []
        for ibar in values:
            if ibar > self.quotes_count:
                return strings
            dt_tick = fromtimestamp(Quotes[int(ibar)].time)
            strings.append(dt_tick.strftime(self.tick_tpl[s_period]))
        return strings


class CenteredTextItem(QtGui.QGraphicsTextItem):
    def __init__(
        self,
        text='',
        parent=None,
        pos=(0, 0),
        pen=None,
        brush=None,
        valign=None,
        opacity=0.1,
    ):
        super().__init__(text, parent)

        self.pen = pen
        self.brush = brush
        self.opacity = opacity
        self.valign = valign
        self.text_flags = QtCore.Qt.AlignCenter
        self.setPos(*pos)
        self.setFlag(self.ItemIgnoresTransformations)

    def boundingRect(self):  # noqa
        r = super().boundingRect()
        if self.valign == QtCore.Qt.AlignTop:
            return QtCore.QRectF(-r.width() / 2, -37, r.width(), r.height())
        elif self.valign == QtCore.Qt.AlignBottom:
            return QtCore.QRectF(-r.width() / 2, 15, r.width(), r.height())

    def paint(self, p, option, widget):
        p.setRenderHint(p.Antialiasing, False)
        p.setRenderHint(p.TextAntialiasing, True)
        p.setPen(self.pen)
        if self.brush.style() != QtCore.Qt.NoBrush:
            p.setOpacity(self.opacity)
            p.fillRect(option.rect, self.brush)
            p.setOpacity(1)
        p.drawText(option.rect, self.text_flags, self.toPlainText())


class AxisLabel(pg.GraphicsObject):

    bg_color = pg.mkColor('#dbdbdb')
    fg_color = pg.mkColor('#000000')

    def __init__(self, parent=None, digits=0, color=None, opacity=1, **kwargs):
        super().__init__(parent)
        self.parent = parent
        self.opacity = opacity
        self.label_str = ''
        self.digits = digits
        self.quotes_count = len(Quotes) - 1
        if isinstance(color, QtGui.QPen):
            self.bg_color = color.color()
            self.fg_color = pg.mkColor('#ffffff')
        elif isinstance(color, list):
            self.bg_color = {'>0': color[0].color(), '<0': color[1].color()}
            self.fg_color = pg.mkColor('#ffffff')
        self.setFlag(self.ItemIgnoresTransformations)

    def tick_to_string(self, tick_pos):
        raise NotImplementedError()

    def boundingRect(self):  # noqa
        raise NotImplementedError()

    def update_label(self, evt_post, point_view):
        raise NotImplementedError()

    def update_label_test(self, ypos=0, ydata=0):
        self.label_str = self.tick_to_string(ydata)
        height = self.boundingRect().height()
        offset = 0  # if have margins
        new_pos = QtCore.QPointF(0, ypos - height / 2 - offset)
        self.setPos(new_pos)

    def paint(self, p, option, widget):
        p.setRenderHint(p.TextAntialiasing, True)
        p.setPen(self.fg_color)
        if self.label_str:
            if not isinstance(self.bg_color, dict):
                bg_color = self.bg_color
            else:
                if int(self.label_str.replace(' ', '')) > 0:
                    bg_color = self.bg_color['>0']
                else:
                    bg_color = self.bg_color['<0']
            p.setOpacity(self.opacity)
            p.fillRect(option.rect, bg_color)
            p.setOpacity(1)
        p.drawText(option.rect, self.text_flags, self.label_str)


class XAxisLabel(AxisLabel):

    text_flags = (
        QtCore.Qt.TextDontClip | QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop
    )

    def tick_to_string(self, tick_pos):
        # TODO: change to actual period
        tpl = self.parent.tick_tpl['D1']
        return fromtimestamp(Quotes[round(tick_pos)].time).strftime(tpl)

    def boundingRect(self):  # noqa
        return QtCore.QRectF(0, 0, 60, 38)

    def update_label(self, evt_post, point_view):
        ibar = point_view.x()
        if ibar > self.quotes_count:
            return
        self.label_str = self.tick_to_string(ibar)
        width = self.boundingRect().width()
        offset = 0  # if have margins
        new_pos = QtCore.QPointF(evt_post.x() - width / 2 - offset, 0)
        self.setPos(new_pos)


class YAxisLabel(AxisLabel):

    text_flags = (
        QtCore.Qt.TextDontClip | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
    )

    def tick_to_string(self, tick_pos):
        return ('{: ,.%df}' % self.digits).format(tick_pos).replace(',', ' ')

    def boundingRect(self):  # noqa
        return QtCore.QRectF(0, 0, 74, 24)

    def update_label(self, evt_post, point_view):
        self.label_str = self.tick_to_string(point_view.y())
        height = self.boundingRect().height()
        offset = 0  # if have margins
        new_pos = QtCore.QPointF(0, evt_post.y() - height / 2 - offset)
        self.setPos(new_pos)


class CustomPlotWidget(pg.PlotWidget):
    sig_mouse_leave = QtCore.Signal(object)
    sig_mouse_enter = QtCore.Signal(object)

    def enterEvent(self, ev):  # noqa
        self.sig_mouse_enter.emit(self)

    def leaveEvent(self, ev):  # noqa
        self.sig_mouse_leave.emit(self)
        self.scene().leaveEvent(ev)


class CrossHairItem(pg.GraphicsObject):
    def __init__(self, parent, indicators=None, digits=0):
        super().__init__()
        self.pen = pg.mkPen('#000000')
        self.parent = parent
        self.indicators = {}
        self.activeIndicator = None
        self.xaxis = self.parent.getAxis('bottom')
        self.yaxis = self.parent.getAxis('right')

        self.vline = self.parent.addLine(x=0, pen=self.pen, movable=False)
        self.hline = self.parent.addLine(y=0, pen=self.pen, movable=False)

        self.proxy_moved = pg.SignalProxy(
            self.parent.scene().sigMouseMoved,
            rateLimit=60,
            slot=self.mouseMoved,
        )

        self.yaxis_label = YAxisLabel(
            parent=self.yaxis, digits=digits, opacity=1
        )

        indicators = indicators or []
        if indicators:
            last_ind = indicators[-1]
            self.xaxis_label = XAxisLabel(
                parent=last_ind.getAxis('bottom'), opacity=1
            )
            self.proxy_enter = pg.SignalProxy(
                self.parent.sig_mouse_enter,
                rateLimit=60,
                slot=lambda: self.mouseAction('Enter', False),
            )
            self.proxy_leave = pg.SignalProxy(
                self.parent.sig_mouse_leave,
                rateLimit=60,
                slot=lambda: self.mouseAction('Leave', False),
            )
        else:
            self.xaxis_label = XAxisLabel(parent=self.xaxis, opacity=1)

        for i in indicators:
            vl = i.addLine(x=0, pen=self.pen, movable=False)
            hl = i.addLine(y=0, pen=self.pen, movable=False)
            yl = YAxisLabel(parent=i.getAxis('right'), opacity=1)
            px_moved = pg.SignalProxy(
                i.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved
            )
            px_enter = pg.SignalProxy(
                i.sig_mouse_enter,
                rateLimit=60,
                slot=lambda: self.mouseAction('Enter', i),
            )
            px_leave = pg.SignalProxy(
                i.sig_mouse_leave,
                rateLimit=60,
                slot=lambda: self.mouseAction('Leave', i),
            )
            self.indicators[i] = {
                'vl': vl,
                'hl': hl,
                'yl': yl,
                'px': (px_moved, px_enter, px_leave),
            }

    def mouseAction(self, action, ind=False):  # noqa
        if action == 'Enter':
            if ind:
                self.indicators[ind]['hl'].show()
                self.indicators[ind]['yl'].show()
                self.activeIndicator = ind
            else:
                self.yaxis_label.show()
                self.hline.show()
        else:  # Leave
            if ind:
                self.indicators[ind]['hl'].hide()
                self.indicators[ind]['yl'].hide()
                self.activeIndicator = None
            else:
                self.yaxis_label.hide()
                self.hline.hide()

    def mouseMoved(self, evt):  # noqa
        pos = evt[0]
        if self.parent.sceneBoundingRect().contains(pos):
            # mouse_point = self.vb.mapSceneToView(pos)
            mouse_point = self.parent.mapToView(pos)
            self.vline.setX(mouse_point.x())
            self.xaxis_label.update_label(evt_post=pos, point_view=mouse_point)
            for opts in self.indicators.values():
                opts['vl'].setX(mouse_point.x())

            if self.activeIndicator:
                mouse_point_ind = self.activeIndicator.mapToView(pos)
                self.indicators[self.activeIndicator]['hl'].setY(
                    mouse_point_ind.y()
                )
                self.indicators[self.activeIndicator]['yl'].update_label(
                    evt_post=pos, point_view=mouse_point_ind
                )
            else:
                self.hline.setY(mouse_point.y())
                self.yaxis_label.update_label(
                    evt_post=pos, point_view=mouse_point
                )

    def paint(self, p, *args):
        pass

    def boundingRect(self):
        return self.parent.boundingRect()


class BarItem(pg.GraphicsObject):

    w = 0.35
    bull_brush = pg.mkBrush('#00cc00')
    bear_brush = pg.mkBrush('#fa0000')

    def __init__(self):
        super().__init__()
        self.generatePicture()

    def _generate(self, p):
        hl = np.array(
            [QtCore.QLineF(q.id, q.low, q.id, q.high) for q in Quotes]
        )
        op = np.array(
            [QtCore.QLineF(q.id - self.w, q.open, q.id, q.open) for q in Quotes]
        )
        cl = np.array(
            [
                QtCore.QLineF(q.id + self.w, q.close, q.id, q.close)
                for q in Quotes
            ]
        )
        lines = np.concatenate([hl, op, cl])
        long_bars = np.resize(Quotes.close > Quotes.open, len(lines))
        short_bars = np.resize(Quotes.close < Quotes.open, len(lines))

        p.setPen(self.bull_brush)
        p.drawLines(*lines[long_bars])

        p.setPen(self.bear_brush)
        p.drawLines(*lines[short_bars])

    @timeit
    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        self._generate(p)
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class CandlestickItem(BarItem):

    w2 = 0.7
    line_pen = pg.mkPen('#000000')
    bull_brush = pg.mkBrush('#00ff00')
    bear_brush = pg.mkBrush('#ff0000')

    def _generate(self, p):
        rects = np.array(
            [
                QtCore.QRectF(q.id - self.w, q.open, self.w2, q.close - q.open)
                for q in Quotes
            ]
        )

        p.setPen(self.line_pen)
        p.drawLines([QtCore.QLineF(q.id, q.low, q.id, q.high) for q in Quotes])

        p.setBrush(self.bull_brush)
        p.drawRects(*rects[Quotes.close > Quotes.open])

        p.setBrush(self.bear_brush)
        p.drawRects(*rects[Quotes.close < Quotes.open])


class QuotesChart(QtGui.QWidget):

    long_pen = pg.mkPen('#006000')
    long_brush = pg.mkBrush('#00ff00')
    short_pen = pg.mkPen('#600000')
    short_brush = pg.mkBrush('#ff0000')

    zoomIsDisabled = QtCore.pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.signals_visible = False
        self.style = ChartType.CANDLESTICK
        self.indicators = []

        self.xaxis = DateAxis(orientation='bottom')
        self.xaxis.setStyle(
            tickTextOffset=7, textFillLimits=[(0, 0.80)], showValues=False
        )

        self.xaxis_ind = DateAxis(orientation='bottom')
        self.xaxis_ind.setStyle(tickTextOffset=7, textFillLimits=[(0, 0.80)])

        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitter.setHandleWidth(4)

        self.layout.addWidget(self.splitter)

    def _show_text_signals(self, lbar, rbar):
        signals = [
            sig
            for sig in self.signals_text_items[lbar:rbar]
            if isinstance(sig, CenteredTextItem)
        ]
        if len(signals) <= 50:
            for sig in signals:
                sig.show()
        else:
            for sig in signals:
                sig.hide()

    def _remove_signals(self):
        self.chart.removeItem(self.signals_group_arrow)
        self.chart.removeItem(self.signals_group_text)
        del self.signals_text_items
        del self.signals_group_arrow
        del self.signals_group_text
        self.signals_visible = False

    def _update_quotes_chart(self):
        self.chart.hideAxis('left')
        self.chart.showAxis('right')
        self.chart.addItem(_get_chart_points(self.style))
        self.chart.setLimits(
            xMin=Quotes[0].id,
            xMax=Quotes[-1].id,
            minXRange=60,
            yMin=Quotes.low.min() * 0.98,
            yMax=Quotes.high.max() * 1.02,
        )
        self.chart.showGrid(x=True, y=True)
        self.chart.setCursor(QtCore.Qt.BlankCursor)
        self.chart.sigXRangeChanged.connect(self._update_yrange_limits)

    def _update_ind_charts(self):
        for ind, d in self.indicators:
            curve = pg.PlotDataItem(d, pen='b', antialias=True)
            ind.addItem(curve)
            ind.hideAxis('left')
            ind.showAxis('right')
            # ind.setAspectLocked(1)
            ind.setXLink(self.chart)
            ind.setLimits(
                xMin=Quotes[0].id,
                xMax=Quotes[-1].id,
                minXRange=60,
                yMin=Quotes.open.min() * 0.98,
                yMax=Quotes.open.max() * 1.02,
            )
            ind.showGrid(x=True, y=True)
            ind.setCursor(QtCore.Qt.BlankCursor)

    def _update_sizes(self):
        min_h_ind = int(self.height() * 0.3 / len(self.indicators))
        sizes = [int(self.height() * 0.7)]
        sizes.extend([min_h_ind] * len(self.indicators))
        self.splitter.setSizes(sizes)  # , int(self.height()*0.2)

    def _update_yrange_limits(self):
        vr = self.chart.viewRect()
        lbar, rbar = int(vr.left()), int(vr.right())
        if self.signals_visible:
            self._show_text_signals(lbar, rbar)
        bars = Quotes[lbar:rbar]
        ylow = bars.low.min() * 0.98
        yhigh = bars.high.max() * 1.02

        std = np.std(bars.close)
        self.chart.setLimits(yMin=ylow, yMax=yhigh, minYRange=std)
        self.chart.setYRange(ylow, yhigh)
        for i, d in self.indicators:
            # ydata = i.plotItem.items[0].getData()[1]
            ydata = d[lbar:rbar]
            ylow = ydata.min() * 0.98
            yhigh = ydata.max() * 1.02
            std = np.std(ydata)
            i.setLimits(yMin=ylow, yMax=yhigh, minYRange=std)
            i.setYRange(ylow, yhigh)

    def plot(self, symbol):
        self.digits = symbol.digits
        self.chart = CustomPlotWidget(
            parent=self.splitter,
            axisItems={'bottom': self.xaxis, 'right': PriceAxis()},
            enableMenu=False,
        )
        self.chart.getPlotItem().setContentsMargins(*CHART_MARGINS)
        self.chart.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)

        inds = [Quotes.open]

        for d in inds:
            ind = CustomPlotWidget(
                parent=self.splitter,
                axisItems={'bottom': self.xaxis_ind, 'right': PriceAxis()},
                enableMenu=False,
            )
            ind.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
            ind.getPlotItem().setContentsMargins(*CHART_MARGINS)
            # self.splitter.addWidget(ind)
            self.indicators.append((ind, d))

        self._update_quotes_chart()
        self._update_ind_charts()
        self._update_sizes()

        ch = CrossHairItem(
            self.chart, [_ind for _ind, d in self.indicators], self.digits
        )
        self.chart.addItem(ch)

    def add_signals(self):
        self.signals_group_text = QtGui.QGraphicsItemGroup()
        self.signals_group_arrow = QtGui.QGraphicsItemGroup()
        self.signals_text_items = np.empty(len(Quotes), dtype=object)

        for p in Portfolio.positions:
            x, price = p.id_bar_open, p.open_price
            if p.type == Order.BUY:
                y = Quotes[x].low * 0.99
                pg.ArrowItem(
                    parent=self.signals_group_arrow,
                    pos=(x, y),
                    pen=self.long_pen,
                    brush=self.long_brush,
                    angle=90,
                    headLen=12,
                    tipAngle=50,
                )
                text_sig = CenteredTextItem(
                    parent=self.signals_group_text,
                    pos=(x, y),
                    pen=self.long_pen,
                    brush=self.long_brush,
                    text=('Buy at {:.%df}' % self.digits).format(price),
                    valign=QtCore.Qt.AlignBottom,
                )
                text_sig.hide()
            else:
                y = Quotes[x].high * 1.01
                pg.ArrowItem(
                    parent=self.signals_group_arrow,
                    pos=(x, y),
                    pen=self.short_pen,
                    brush=self.short_brush,
                    angle=-90,
                    headLen=12,
                    tipAngle=50,
                )
                text_sig = CenteredTextItem(
                    parent=self.signals_group_text,
                    pos=(x, y),
                    pen=self.short_pen,
                    brush=self.short_brush,
                    text=('Sell at {:.%df}' % self.digits).format(price),
                    valign=QtCore.Qt.AlignTop,
                )
                text_sig.hide()

            self.signals_text_items[x] = text_sig

        self.chart.addItem(self.signals_group_arrow)
        self.chart.addItem(self.signals_group_text)
        self.signals_visible = True


class EquityChart(QtGui.QWidget):

    eq_pen_pos_color = pg.mkColor('#00cc00')
    eq_pen_neg_color = pg.mkColor('#cc0000')
    eq_brush_pos_color = pg.mkColor('#40ee40')
    eq_brush_neg_color = pg.mkColor('#ee4040')
    long_pen_color = pg.mkColor('#008000')
    short_pen_color = pg.mkColor('#800000')
    buy_and_hold_pen_color = pg.mkColor('#4444ff')

    def __init__(self):
        super().__init__()
        self.xaxis = DateAxis(orientation='bottom')
        self.xaxis.setStyle(tickTextOffset=7, textFillLimits=[(0, 0.80)])
        self.yaxis = PriceAxis()

        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.chart = pg.PlotWidget(
            axisItems={'bottom': self.xaxis, 'right': self.yaxis},
            enableMenu=False,
        )
        self.chart.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
        self.chart.getPlotItem().setContentsMargins(*CHART_MARGINS)
        self.chart.showGrid(x=True, y=True)
        self.chart.hideAxis('left')
        self.chart.showAxis('right')

        self.chart.setCursor(QtCore.Qt.BlankCursor)
        self.chart.sigXRangeChanged.connect(self._update_yrange_limits)

        self.layout.addWidget(self.chart)

    def _add_legend(self):
        legend = pg.LegendItem((140, 100), offset=(10, 10))
        legend.setParentItem(self.chart.getPlotItem())

        for arr, item in self.curves:
            legend.addItem(
                SampleLegendItem(item),
                item.opts['name']
                if not isinstance(item, tuple)
                else item[0].opts['name'],
            )

    def _add_ylabels(self):
        self.ylabels = []
        for arr, item in self.curves:
            color = (
                item.opts['pen']
                if not isinstance(item, tuple)
                else [i.opts['pen'] for i in item]
            )
            label = YAxisLabel(parent=self.yaxis, color=color)
            self.ylabels.append(label)

    def _update_ylabels(self, vb, rbar):
        for i, curve in enumerate(self.curves):
            arr, item = curve
            ylast = arr[rbar]
            ypos = vb.mapFromView(QtCore.QPointF(0, ylast)).y()
            axlabel = self.ylabels[i]
            axlabel.update_label_test(ypos=ypos, ydata=ylast)

    def _update_yrange_limits(self, vb=None):
        if not hasattr(self, 'min_curve'):
            return
        vr = self.chart.viewRect()
        lbar, rbar = int(vr.left()), int(vr.right())
        ylow = self.min_curve[lbar:rbar].min() * 1.1
        yhigh = self.max_curve[lbar:rbar].max() * 1.1

        std = np.std(self.max_curve[lbar:rbar]) * 4
        self.chart.setLimits(yMin=ylow, yMax=yhigh, minYRange=std)
        self.chart.setYRange(ylow, yhigh)
        self._update_ylabels(vb, rbar)

    @timeit
    def plot(self):
        equity_curve = Portfolio.equity_curve
        eq_pos = np.zeros_like(equity_curve)
        eq_neg = np.zeros_like(equity_curve)
        eq_pos[equity_curve >= 0] = equity_curve[equity_curve >= 0]
        eq_neg[equity_curve <= 0] = equity_curve[equity_curve <= 0]

        # Equity
        self.eq_pos_curve = pg.PlotCurveItem(
            eq_pos,
            name='Equity',
            fillLevel=0,
            antialias=True,
            pen=self.eq_pen_pos_color,
            brush=self.eq_brush_pos_color,
        )
        self.eq_neg_curve = pg.PlotCurveItem(
            eq_neg,
            name='Equity',
            fillLevel=0,
            antialias=True,
            pen=self.eq_pen_neg_color,
            brush=self.eq_brush_neg_color,
        )
        self.chart.addItem(self.eq_pos_curve)
        self.chart.addItem(self.eq_neg_curve)

        # Only Long
        self.long_curve = pg.PlotCurveItem(
            Portfolio.long_curve,
            name='Only Long',
            pen=self.long_pen_color,
            antialias=True,
        )
        self.chart.addItem(self.long_curve)

        # Only Short
        self.short_curve = pg.PlotCurveItem(
            Portfolio.short_curve,
            name='Only Short',
            pen=self.short_pen_color,
            antialias=True,
        )
        self.chart.addItem(self.short_curve)

        # Buy and Hold
        self.buy_and_hold_curve = pg.PlotCurveItem(
            Portfolio.buy_and_hold_curve,
            name='Buy and Hold',
            pen=self.buy_and_hold_pen_color,
            antialias=True,
        )
        self.chart.addItem(self.buy_and_hold_curve)

        self.curves = [
            (Portfolio.equity_curve, (self.eq_pos_curve, self.eq_neg_curve)),
            (Portfolio.long_curve, self.long_curve),
            (Portfolio.short_curve, self.short_curve),
            (Portfolio.buy_and_hold_curve, self.buy_and_hold_curve),
        ]

        self._add_legend()
        self._add_ylabels()

        ch = CrossHairItem(self.chart)
        self.chart.addItem(ch)

        arrs = (
            Portfolio.equity_curve,
            Portfolio.buy_and_hold_curve,
            Portfolio.long_curve,
            Portfolio.short_curve,
        )
        np_arrs = np.concatenate(arrs)
        _min = abs(np_arrs.min()) * -1.1
        _max = np_arrs.max() * 1.1

        self.chart.setLimits(
            xMin=Quotes[0].id,
            xMax=Quotes[-1].id,
            yMin=_min,
            yMax=_max,
            minXRange=60,
        )

        self.min_curve = arrs[0].copy()
        self.max_curve = arrs[0].copy()
        for arr in arrs[1:]:
            self.min_curve = np.minimum(self.min_curve, arr)
            self.max_curve = np.maximum(self.max_curve, arr)


def _get_chart_points(style):
    if style == ChartType.CANDLESTICK:
        return CandlestickItem()
    elif style == ChartType.BAR:
        return BarItem()
    return pg.PlotDataItem(Quotes.close, pen='b')
