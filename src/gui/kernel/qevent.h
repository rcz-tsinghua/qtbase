/****************************************************************************
**
** Copyright (C) 2020 The Qt Company Ltd.
** Contact: https://www.qt.io/licensing/
**
** This file is part of the QtGui module of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:LGPL$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see https://www.qt.io/terms-conditions. For further
** information use the contact form at https://www.qt.io/contact-us.
**
** GNU Lesser General Public License Usage
** Alternatively, this file may be used under the terms of the GNU Lesser
** General Public License version 3 as published by the Free Software
** Foundation and appearing in the file LICENSE.LGPL3 included in the
** packaging of this file. Please review the following information to
** ensure the GNU Lesser General Public License version 3 requirements
** will be met: https://www.gnu.org/licenses/lgpl-3.0.html.
**
** GNU General Public License Usage
** Alternatively, this file may be used under the terms of the GNU
** General Public License version 2.0 or (at your option) the GNU General
** Public license version 3 or any later version approved by the KDE Free
** Qt Foundation. The licenses are as published by the Free Software
** Foundation and appearing in the file LICENSE.GPL2 and LICENSE.GPL3
** included in the packaging of this file. Please review the following
** information to ensure the GNU General Public License requirements will
** be met: https://www.gnu.org/licenses/gpl-2.0.html and
** https://www.gnu.org/licenses/gpl-3.0.html.
**
** $QT_END_LICENSE$
**
****************************************************************************/

#ifndef QEVENT_H
#define QEVENT_H

#include <QtGui/qtguiglobal.h>

#include <QtCore/qcoreevent.h>
#include <QtCore/qiodevice.h>
#include <QtCore/qlist.h>
#include <QtCore/qnamespace.h>
#include <QtCore/qstring.h>
#include <QtCore/qurl.h>
#include <QtCore/qvariant.h>
#include <QtGui/qpointingdevice.h>
#include <QtGui/qregion.h>
#include <QtGui/qvector2d.h>
#include <QtGui/qwindowdefs.h>

#if QT_CONFIG(shortcut)
#  include <QtGui/qkeysequence.h>
#endif

QT_BEGIN_NAMESPACE

class QFile;
class QAction;
class QInputDevice;
class QPointingDevice;
class QScreen;
#if QT_CONFIG(gestures)
class QGesture;
#endif

class Q_GUI_EXPORT QInputEvent : public QEvent
{
public:
    explicit QInputEvent(Type type, const QInputDevice *m_dev, Qt::KeyboardModifiers modifiers = Qt::NoModifier);
    ~QInputEvent();
    const QInputDevice *device() const { return m_dev; }
    QInputDevice::DeviceType deviceType() const { return m_dev ? m_dev->type() : QInputDevice::DeviceType::Unknown; }
    inline Qt::KeyboardModifiers modifiers() const { return modState; }
    inline void setModifiers(Qt::KeyboardModifiers amodifiers) { modState = amodifiers; }
    inline ulong timestamp() const { return ts; }
    inline void setTimestamp(ulong atimestamp) { ts = atimestamp; }
protected:
    const QInputDevice *m_dev = nullptr;
    Qt::KeyboardModifiers modState;
    ulong ts;
};

class Q_GUI_EXPORT QPointerEvent : public QInputEvent
{
public:
    explicit QPointerEvent(Type type, const QPointingDevice *dev, Qt::KeyboardModifiers modifiers = Qt::NoModifier);
    const QPointingDevice *pointingDevice() const;
    QPointingDevice::PointerType pointerType() const {
        return pointingDevice() ? pointingDevice()->pointerType() : QPointingDevice::PointerType::Unknown;
    }
};

class Q_GUI_EXPORT QEnterEvent : public QEvent
{
public:
    QEnterEvent(const QPointF &localPos, const QPointF &scenePos, const QPointF &globalPos);
    ~QEnterEvent();

#if QT_DEPRECATED_SINCE(6, 0)
#ifndef QT_NO_INTEGER_EVENT_COORDINATES
    QT_DEPRECATED_VERSION_X_6_0("Use position()")
    inline QPoint pos() const { return position().toPoint(); }
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition()")
    inline QPoint globalPos() const { return globalPosition().toPoint(); }
    QT_DEPRECATED_VERSION_X_6_0("Use position()")
    inline int x() const { return qRound(position().x()); }
    QT_DEPRECATED_VERSION_X_6_0("Use position()")
    inline int y() const { return qRound(position().y()); }
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition()")
    inline int globalX() const { return qRound(globalPosition().x()); }
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition()")
    inline int globalY() const { return qRound(globalPosition().y()); }
#endif
    QT_DEPRECATED_VERSION_X_6_0("Use position()")
    QPointF localPos() const { return position(); }
    QT_DEPRECATED_VERSION_X_6_0("Use scenePosition()")
    QPointF windowPos() const { return scenePosition(); }
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition()")
    QPointF screenPos() const { return globalPosition(); }
#endif // QT_DEPRECATED_SINCE(6, 0)

    QPointF position() const { return l; }
    QPointF scenePosition() const { return s; }
    QPointF globalPosition() const { return g; }

protected:
    QPointF l, s, g;
};

class Q_GUI_EXPORT QMouseEvent : public QPointerEvent
{
public:
    QMouseEvent(Type type, const QPointF &localPos, Qt::MouseButton button,
                Qt::MouseButtons buttons, Qt::KeyboardModifiers modifiers);
    QMouseEvent(Type type, const QPointF &localPos, const QPointF &globalPos,
                Qt::MouseButton button, Qt::MouseButtons buttons,
                Qt::KeyboardModifiers modifiers);
    QMouseEvent(Type type, const QPointF &localPos, const QPointF &scenePos, const QPointF &globalPos,
                Qt::MouseButton button, Qt::MouseButtons buttons,
                Qt::KeyboardModifiers modifiers);
    QMouseEvent(Type type, const QPointF &localPos, const QPointF &scenePos, const QPointF &globalPos,
                Qt::MouseButton button, Qt::MouseButtons buttons,
                Qt::KeyboardModifiers modifiers, Qt::MouseEventSource source);
    ~QMouseEvent();

#ifndef QT_NO_INTEGER_EVENT_COORDINATES
    inline QPoint pos() const { return position().toPoint(); }
#endif
#if QT_DEPRECATED_SINCE(6, 0)
#ifndef QT_NO_INTEGER_EVENT_COORDINATES
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition()")
    inline QPoint globalPos() const { return globalPosition().toPoint(); }
    QT_DEPRECATED_VERSION_X_6_0("Use position()")
    inline int x() const { return qRound(position().x()); }
    QT_DEPRECATED_VERSION_X_6_0("Use position()")
    inline int y() const { return qRound(position().y()); }
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition()")
    inline int globalX() const { return qRound(globalPosition().x()); }
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition()")
    inline int globalY() const { return qRound(globalPosition().y()); }
#endif // QT_NO_INTEGER_EVENT_COORDINATES
    QT_DEPRECATED_VERSION_X_6_0("Use position()")
    QPointF localPos() const { return position(); }
    QT_DEPRECATED_VERSION_X_6_0("Use scenePosition()")
    QPointF windowPos() const { return scenePosition(); }
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition()")
    QPointF screenPos() const { return globalPosition(); }
#endif // QT_DEPRECATED_SINCE(6, 0)

    QPointF position() const { return l; }
    QPointF scenePosition() const { return w; }
    QPointF globalPosition() const { return g; }

    inline Qt::MouseButton button() const { return b; }
    inline Qt::MouseButtons buttons() const { return mouseState; }

    inline void setLocalPos(const QPointF &localPosition) { l = localPosition; }

    Qt::MouseEventSource source() const;
    Qt::MouseEventFlags flags() const;

protected:
    QPointF l, w, g;
    Qt::MouseButton b;
    Qt::MouseButtons mouseState;
    int caps;
    QVector2D velocity;

    friend class QGuiApplicationPrivate;
};

class Q_GUI_EXPORT QHoverEvent : public QInputEvent
{
public:
    QHoverEvent(Type type, const QPointF &pos, const QPointF &oldPos, Qt::KeyboardModifiers modifiers = Qt::NoModifier);
    ~QHoverEvent();

#if QT_DEPRECATED_SINCE(6, 0)
#ifndef QT_NO_INTEGER_EVENT_COORDINATES
    QT_DEPRECATED_VERSION_X_6_0("Use position()")
    inline QPoint pos() const { return position().toPoint(); }
#endif

    QT_DEPRECATED_VERSION_X_6_0("Use position()")
    inline QPointF posF() const { return position(); }
#endif // QT_DEPRECATED_SINCE(6, 0)

    // TODO deprecate when we figure out an actual replacement (point history?)
    inline QPoint oldPos() const { return op.toPoint(); }
    inline QPointF oldPosF() const { return op; }

    QPointF position() const { return p; }

protected:
    QPointF p, op;
};

#if QT_CONFIG(wheelevent)
class Q_GUI_EXPORT QWheelEvent : public QPointerEvent
{
public:
    enum { DefaultDeltasPerStep = 120 };

    QWheelEvent(QPointF pos, QPointF globalPos, QPoint pixelDelta, QPoint angleDelta,
                Qt::MouseButtons buttons, Qt::KeyboardModifiers modifiers, Qt::ScrollPhase phase,
                bool inverted, Qt::MouseEventSource source = Qt::MouseEventNotSynthesized);
    ~QWheelEvent();


    inline QPoint pixelDelta() const { return pixelD; }
    inline QPoint angleDelta() const { return angleD; }

    inline QPointF position() const { return p; }
    inline QPointF globalPosition() const { return g; }

    inline Qt::MouseButtons buttons() const { return mouseState; }

    inline Qt::ScrollPhase phase() const { return Qt::ScrollPhase(ph); }
    inline bool inverted() const { return invertedScrolling; }

    Qt::MouseEventSource source() const { return Qt::MouseEventSource(src); }

protected:
    QPointF p;
    QPointF g;
    QPoint pixelD;
    QPoint angleD;
    Qt::MouseButtons mouseState;
    uint src: 2;
    uint ph : 3;
    bool invertedScrolling : 1;
    int reserved : 26;

    friend class QApplication;
};
#endif

#if QT_CONFIG(tabletevent)
class Q_GUI_EXPORT QTabletEvent : public QPointerEvent
{
    Q_GADGET
public:
    QTabletEvent(Type t, const QPointF &pos, const QPointF &globalPos,
                 int deviceType, int pointerType, qreal pressure, int xTilt, int yTilt,
                 qreal tangentialPressure, qreal rotation, int z,
                 Qt::KeyboardModifiers keyState, qint64 uniqueID,
                 Qt::MouseButton button, Qt::MouseButtons buttons);
    QTabletEvent(Type t, const QPointingDevice *dev, const QPointF &pos, const QPointF &globalPos,
                 qreal pressure, int xTilt, int yTilt,
                 qreal tangentialPressure, qreal rotation, int z,
                 Qt::KeyboardModifiers keyState,
                 Qt::MouseButton button, Qt::MouseButtons buttons);
    ~QTabletEvent();

#if QT_DEPRECATED_SINCE(6, 0)
    QT_DEPRECATED_VERSION_X_6_0("Use position()")
    inline QPoint pos() const { return position().toPoint(); }
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition()")
    inline QPoint globalPos() const { return globalPosition().toPoint(); }

    QT_DEPRECATED_VERSION_X_6_0("Use position()")
    inline const QPointF posF() const { return position(); }
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition()")
    inline const QPointF globalPosF() const { return globalPosition(); }
    QT_DEPRECATED_VERSION_X_6_0("Use position().x()")
    inline int x() const { return qRound(position().x()); }
    QT_DEPRECATED_VERSION_X_6_0("Use position().y()")
    inline int y() const { return qRound(position().y()); }
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition().x()")
    inline int globalX() const { return qRound(globalPosition().x()); }
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition().y()")
    inline int globalY() const { return qRound(globalPosition().y()); }
    QT_DEPRECATED_VERSION_X_6_0("use globalPosition().x()")
    inline qreal hiResGlobalX() const { return globalPosition().x(); }
    QT_DEPRECATED_VERSION_X_6_0("use globalPosition().y()")
    inline qreal hiResGlobalY() const { return globalPosition().y(); }
#endif
    inline QPointF position() const { return mPos; }
    inline QPointF globalPosition() const { return mGPos; }
    inline qint64 uniqueId() const { return pointingDevice() ? pointingDevice()->uniqueId().numericId() : -1; }
    inline qreal pressure() const { return mPress; }
    inline int z() const { return mZ; }
    inline qreal tangentialPressure() const { return mTangential; }
    inline qreal rotation() const { return mRot; }
    inline int xTilt() const { return mXT; }
    inline int yTilt() const { return mYT; }
    inline Qt::MouseButton button() const { return mButton; }
    inline Qt::MouseButtons buttons() const { return mButtons; }

protected:
    QPointF mPos, mGPos;
    int mXT, mYT, mZ;
    qreal mPress, mTangential, mRot;
    // TODO refactor to parent class along with QMouseEvent's button storage
    Qt::MouseButton mButton;
    Qt::MouseButtons mButtons;
};
#endif // QT_CONFIG(tabletevent)

#if QT_CONFIG(gestures)
class Q_GUI_EXPORT QNativeGestureEvent : public QPointerEvent
{
public:
    QNativeGestureEvent(Qt::NativeGestureType type, const QPointingDevice *dev, const QPointF &localPos, const QPointF &scenePos,
                        const QPointF &globalPos, qreal value, ulong sequenceId, quint64 intArgument);
    ~QNativeGestureEvent();
    Qt::NativeGestureType gestureType() const { return mGestureType; }
    qreal value() const { return mRealValue; }

#if QT_DEPRECATED_SINCE(6, 0)
#ifndef QT_NO_INTEGER_EVENT_COORDINATES
    QT_DEPRECATED_VERSION_X_6_0("Use position().toPoint()")
    inline const QPoint pos() const { return position().toPoint(); }
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition().toPoint()")
    inline const QPoint globalPos() const { return globalPosition().toPoint(); }
#endif
    QT_DEPRECATED_VERSION_X_6_0("Use position()")
    QPointF localPos() const { return position(); }
    QT_DEPRECATED_VERSION_X_6_0("Use scenePosition()")
    QPointF windowPos() const { return scenePosition(); }
    QT_DEPRECATED_VERSION_X_6_0("Use globalPosition()")
    QPointF screenPos() const { return globalPosition(); }
#endif

    QPointF position() const { return mLocalPos; }
    QPointF scenePosition() const { return mScenePos; }
    QPointF globalPosition() const { return mGlobalPos; }

protected:
    Qt::NativeGestureType mGestureType;
    QPointF mLocalPos;
    QPointF mScenePos;
    QPointF mGlobalPos;
    qreal mRealValue;
    ulong mSequenceId;
    quint64 mIntValue;
};
#endif // QT_CONFIG(gestures)

class Q_GUI_EXPORT QKeyEvent : public QInputEvent
{
public:
    QKeyEvent(Type type, int key, Qt::KeyboardModifiers modifiers, const QString& text = QString(),
              bool autorep = false, ushort count = 1);
    QKeyEvent(Type type, int key, Qt::KeyboardModifiers modifiers,
              quint32 nativeScanCode, quint32 nativeVirtualKey, quint32 nativeModifiers,
              const QString &text = QString(), bool autorep = false, ushort count = 1);
    ~QKeyEvent();

    int key() const { return k; }
#if QT_CONFIG(shortcut)
    bool matches(QKeySequence::StandardKey key) const;
#endif
    Qt::KeyboardModifiers modifiers() const;
    inline QString text() const { return txt; }
    inline bool isAutoRepeat() const { return autor; }
    inline int count() const { return int(c); }

    inline quint32 nativeScanCode() const { return nScanCode; }
    inline quint32 nativeVirtualKey() const { return nVirtualKey; }
    inline quint32 nativeModifiers() const { return nModifiers; }

protected:
    QString txt;
    int k;
    quint32 nScanCode;
    quint32 nVirtualKey;
    quint32 nModifiers;
    ushort c;
    ushort autor:1;
    // ushort reserved:15;
};


class Q_GUI_EXPORT QFocusEvent : public QEvent
{
public:
    explicit QFocusEvent(Type type, Qt::FocusReason reason=Qt::OtherFocusReason);
    ~QFocusEvent();

    inline bool gotFocus() const { return type() == FocusIn; }
    inline bool lostFocus() const { return type() == FocusOut; }

    Qt::FocusReason reason() const;

private:
    Qt::FocusReason m_reason;
};


class Q_GUI_EXPORT QPaintEvent : public QEvent
{
public:
    explicit QPaintEvent(const QRegion& paintRegion);
    explicit QPaintEvent(const QRect &paintRect);
    ~QPaintEvent();

    inline const QRect &rect() const { return m_rect; }
    inline const QRegion &region() const { return m_region; }

protected:
    QRect m_rect;
    QRegion m_region;
    bool m_erased;
};

class Q_GUI_EXPORT QMoveEvent : public QEvent
{
public:
    QMoveEvent(const QPoint &pos, const QPoint &oldPos);
    ~QMoveEvent();

    inline const QPoint &pos() const { return p; }
    inline const QPoint &oldPos() const { return oldp;}
protected:
    QPoint p, oldp;
    friend class QApplication;
};

class Q_GUI_EXPORT QExposeEvent : public QEvent
{
public:
    explicit QExposeEvent(const QRegion &rgn);
    ~QExposeEvent();

    inline const QRegion &region() const { return rgn; }

protected:
    QRegion rgn;
};

class Q_GUI_EXPORT QPlatformSurfaceEvent : public QEvent
{
public:
    enum SurfaceEventType {
        SurfaceCreated,
        SurfaceAboutToBeDestroyed
    };

    explicit QPlatformSurfaceEvent(SurfaceEventType surfaceEventType);
    ~QPlatformSurfaceEvent();

    inline SurfaceEventType surfaceEventType() const { return m_surfaceEventType; }

protected:
    SurfaceEventType m_surfaceEventType;
};

class Q_GUI_EXPORT QResizeEvent : public QEvent
{
public:
    QResizeEvent(const QSize &size, const QSize &oldSize);
    ~QResizeEvent();

    inline const QSize &size() const { return s; }
    inline const QSize &oldSize()const { return olds;}
protected:
    QSize s, olds;
    friend class QApplication;
};


class Q_GUI_EXPORT QCloseEvent : public QEvent
{
public:
    QCloseEvent();
    ~QCloseEvent();
};


class Q_GUI_EXPORT QIconDragEvent : public QEvent
{
public:
    QIconDragEvent();
    ~QIconDragEvent();
};


class Q_GUI_EXPORT QShowEvent : public QEvent
{
public:
    QShowEvent();
    ~QShowEvent();
};


class Q_GUI_EXPORT QHideEvent : public QEvent
{
public:
    QHideEvent();
    ~QHideEvent();
};

#ifndef QT_NO_CONTEXTMENU
class Q_GUI_EXPORT QContextMenuEvent : public QInputEvent
{
public:
    enum Reason { Mouse, Keyboard, Other };

    QContextMenuEvent(Reason reason, const QPoint &pos, const QPoint &globalPos,
                      Qt::KeyboardModifiers modifiers);
    QContextMenuEvent(Reason reason, const QPoint &pos, const QPoint &globalPos);
    QContextMenuEvent(Reason reason, const QPoint &pos);
    ~QContextMenuEvent();

    inline int x() const { return p.x(); }
    inline int y() const { return p.y(); }
    inline int globalX() const { return gp.x(); }
    inline int globalY() const { return gp.y(); }

    inline const QPoint& pos() const { return p; }
    inline const QPoint& globalPos() const { return gp; }

    inline Reason reason() const { return Reason(reas); }

protected:
    QPoint p;
    QPoint gp;
    uint reas : 8;
};
#endif // QT_NO_CONTEXTMENU

#ifndef QT_NO_INPUTMETHOD
class Q_GUI_EXPORT QInputMethodEvent : public QEvent
{
public:
    enum AttributeType {
       TextFormat,
       Cursor,
       Language,
       Ruby,
       Selection
    };
    class Attribute {
    public:
        Attribute(AttributeType typ, int s, int l, QVariant val) : type(typ), start(s), length(l), value(std::move(val)) {}
        Attribute(AttributeType typ, int s, int l) : type(typ), start(s), length(l), value() {}

        AttributeType type;
        int start;
        int length;
        QVariant value;
    };
    QInputMethodEvent();
    QInputMethodEvent(const QString &preeditText, const QList<Attribute> &attributes);
    ~QInputMethodEvent();

    void setCommitString(const QString &commitString, int replaceFrom = 0, int replaceLength = 0);
    inline const QList<Attribute> &attributes() const { return attrs; }
    inline const QString &preeditString() const { return preedit; }

    inline const QString &commitString() const { return commit; }
    inline int replacementStart() const { return replace_from; }
    inline int replacementLength() const { return replace_length; }

    QInputMethodEvent(const QInputMethodEvent &other);

private:
    QString preedit;
    QList<Attribute> attrs;
    QString commit;
    int replace_from;
    int replace_length;
};
Q_DECLARE_TYPEINFO(QInputMethodEvent::Attribute, Q_MOVABLE_TYPE);

class Q_GUI_EXPORT QInputMethodQueryEvent : public QEvent
{
public:
    explicit QInputMethodQueryEvent(Qt::InputMethodQueries queries);
    ~QInputMethodQueryEvent();

    Qt::InputMethodQueries queries() const { return m_queries; }

    void setValue(Qt::InputMethodQuery query, const QVariant &value);
    QVariant value(Qt::InputMethodQuery query) const;
private:
    Qt::InputMethodQueries m_queries;
    struct QueryPair {
        Qt::InputMethodQuery query;
        QVariant value;
    };
    friend QTypeInfo<QueryPair>;
    QList<QueryPair> m_values;
};
Q_DECLARE_TYPEINFO(QInputMethodQueryEvent::QueryPair, Q_MOVABLE_TYPE);

#endif // QT_NO_INPUTMETHOD

#if QT_CONFIG(draganddrop)

class QMimeData;

class Q_GUI_EXPORT QDropEvent : public QEvent
{
public:
    QDropEvent(const QPointF& pos, Qt::DropActions actions, const QMimeData *data,
               Qt::MouseButtons buttons, Qt::KeyboardModifiers modifiers, Type type = Drop);
    ~QDropEvent();

#if QT_DEPRECATED_SINCE(6, 0)
    QT_DEPRECATED_VERSION_X_6_0("Use position().toPoint()")
    inline QPoint pos() const { return position().toPoint(); }
    QT_DEPRECATED_VERSION_X_6_0("Use position()")
    inline QPointF posF() const { return position(); }
    QT_DEPRECATED_VERSION_X_6_0("Use buttons()")
    inline Qt::MouseButtons mouseButtons() const { return buttons(); }
    QT_DEPRECATED_VERSION_X_6_0("Use modifiers()")
    inline Qt::KeyboardModifiers keyboardModifiers() const { return modifiers(); }
#endif // QT_DEPRECATED_SINCE(6, 0)

    QPointF position() const { return p; }
    inline Qt::MouseButtons buttons() const { return mouseState; }
    inline Qt::KeyboardModifiers modifiers() const { return modState; }

    inline Qt::DropActions possibleActions() const { return act; }
    inline Qt::DropAction proposedAction() const { return default_action; }
    inline void acceptProposedAction() { drop_action = default_action; accept(); }

    inline Qt::DropAction dropAction() const { return drop_action; }
    void setDropAction(Qt::DropAction action);

    QObject* source() const;
    inline const QMimeData *mimeData() const { return mdata; }

protected:
    friend class QApplication;
    QPointF p;
    Qt::MouseButtons mouseState;
    Qt::KeyboardModifiers modState;
    Qt::DropActions act;
    Qt::DropAction drop_action;
    Qt::DropAction default_action;
    const QMimeData *mdata;
};


class Q_GUI_EXPORT QDragMoveEvent : public QDropEvent
{
public:
    QDragMoveEvent(const QPoint &pos, Qt::DropActions actions, const QMimeData *data,
                   Qt::MouseButtons buttons, Qt::KeyboardModifiers modifiers, Type type = DragMove);
    ~QDragMoveEvent();

    inline QRect answerRect() const { return rect; }

    inline void accept() { QDropEvent::accept(); }
    inline void ignore() { QDropEvent::ignore(); }

    inline void accept(const QRect & r) { accept(); rect = r; }
    inline void ignore(const QRect & r) { ignore(); rect = r; }

protected:
    QRect rect;
};


class Q_GUI_EXPORT QDragEnterEvent : public QDragMoveEvent
{
public:
    QDragEnterEvent(const QPoint &pos, Qt::DropActions actions, const QMimeData *data,
                    Qt::MouseButtons buttons, Qt::KeyboardModifiers modifiers);
    ~QDragEnterEvent();
};


class Q_GUI_EXPORT QDragLeaveEvent : public QEvent
{
public:
    QDragLeaveEvent();
    ~QDragLeaveEvent();
};
#endif // QT_CONFIG(draganddrop)


class Q_GUI_EXPORT QHelpEvent : public QEvent
{
public:
    QHelpEvent(Type type, const QPoint &pos, const QPoint &globalPos);
    ~QHelpEvent();

    inline int x() const { return p.x(); }
    inline int y() const { return p.y(); }
    inline int globalX() const { return gp.x(); }
    inline int globalY() const { return gp.y(); }

    inline const QPoint& pos()  const { return p; }
    inline const QPoint& globalPos() const { return gp; }

private:
    QPoint p;
    QPoint gp;
};

#ifndef QT_NO_STATUSTIP
class Q_GUI_EXPORT QStatusTipEvent : public QEvent
{
public:
    explicit QStatusTipEvent(const QString &tip);
    ~QStatusTipEvent();

    inline QString tip() const { return s; }
private:
    QString s;
};
#endif

#if QT_CONFIG(whatsthis)
class Q_GUI_EXPORT QWhatsThisClickedEvent : public QEvent
{
public:
    explicit QWhatsThisClickedEvent(const QString &href);
    ~QWhatsThisClickedEvent();

    inline QString href() const { return s; }
private:
    QString s;
};
#endif

#if QT_CONFIG(action)
class Q_GUI_EXPORT QActionEvent : public QEvent
{
    QAction *act, *bef;
public:
    QActionEvent(int type, QAction *action, QAction *before = nullptr);
    ~QActionEvent();

    inline QAction *action() const { return act; }
    inline QAction *before() const { return bef; }
};
#endif // QT_CONFIG(action)

class Q_GUI_EXPORT QFileOpenEvent : public QEvent
{
public:
    explicit QFileOpenEvent(const QString &file);
    explicit QFileOpenEvent(const QUrl &url);
    ~QFileOpenEvent();

    inline QString file() const { return f; }
    QUrl url() const { return m_url; }
    bool openFile(QFile &file, QIODevice::OpenMode flags) const;
private:
    QString f;
    QUrl m_url;
};

#ifndef QT_NO_TOOLBAR
class Q_GUI_EXPORT QToolBarChangeEvent : public QEvent
{
public:
    explicit QToolBarChangeEvent(bool t);
    ~QToolBarChangeEvent();

    inline bool toggle() const { return tog; }
private:
    uint tog : 1;
};
#endif

#if QT_CONFIG(shortcut)
class Q_GUI_EXPORT QShortcutEvent : public QEvent
{
public:
    QShortcutEvent(const QKeySequence &key, int id, bool ambiguous = false);
    ~QShortcutEvent();

    inline const QKeySequence &key() const { return sequence; }
    inline int shortcutId() const { return sid; }
    inline bool isAmbiguous() const { return ambig; }
protected:
    QKeySequence sequence;
    bool ambig;
    int  sid;
};
#endif

class Q_GUI_EXPORT QWindowStateChangeEvent: public QEvent
{
public:
    explicit QWindowStateChangeEvent(Qt::WindowStates aOldState, bool isOverride = false);
    ~QWindowStateChangeEvent();

    inline Qt::WindowStates oldState() const { return ostate; }
    bool isOverride() const;

private:
    Qt::WindowStates ostate;
    bool m_override;
};

#ifndef QT_NO_DEBUG_STREAM
Q_GUI_EXPORT QDebug operator<<(QDebug, const QEvent *);
#endif

#if QT_CONFIG(shortcut)
inline bool operator==(QKeyEvent *e, QKeySequence::StandardKey key){return (e ? e->matches(key) : false);}
inline bool operator==(QKeySequence::StandardKey key, QKeyEvent *e){return (e ? e->matches(key) : false);}
#endif // QT_CONFIG(shortcut)

class QTouchEventTouchPointPrivate;
class Q_GUI_EXPORT QTouchEvent : public QPointerEvent
{
public:
    class Q_GUI_EXPORT TouchPoint
    {
    public:
        enum InfoFlag {
            Pen  = 0x0001,
            Token = 0x0002
        };
#ifndef Q_MOC_RUN
        // otherwise moc gives
        // Error: Meta object features not supported for nested classes
        Q_DECLARE_FLAGS(InfoFlags, InfoFlag)
#endif

        explicit TouchPoint(int id = -1);
        TouchPoint(const TouchPoint &other);
        TouchPoint(TouchPoint &&other) noexcept
            : d(nullptr)
        { qSwap(d, other.d); }
        TouchPoint &operator=(TouchPoint &&other) noexcept
        { qSwap(d, other.d); return *this; }
        ~TouchPoint();

        TouchPoint &operator=(const TouchPoint &other)
        { if ( d != other.d ) { TouchPoint copy(other); swap(copy); } return *this; }

        void swap(TouchPoint &other) noexcept
        { qSwap(d, other.d); }

        int id() const;
        QPointingDeviceUniqueId uniqueId() const;

        Qt::TouchPointState state() const;

#if QT_DEPRECATED_SINCE(6, 0)
        QT_DEPRECATED_VERSION_X_6_0("Use position()")
        QPointF pos() const { return position(); }
        QT_DEPRECATED_VERSION_X_6_0("Use pressPosition()")
        QPointF startPos() const { return pressPosition(); }

        QT_DEPRECATED_VERSION_X_6_0("Use scenePosition()")
        QPointF scenePos() const { return scenePosition(); }
        QT_DEPRECATED_VERSION_X_6_0("Use scenePressPosition()")
        QPointF startScenePos() const { return scenePressPosition(); }

        QT_DEPRECATED_VERSION_X_6_0("Use globalPosition()")
        QPointF screenPos() const { return globalPosition(); }
        QT_DEPRECATED_VERSION_X_6_0("Use globalPressPosition()")
        QPointF startScreenPos() const { return globalPressPosition(); }
#endif // QT_DEPRECATED_SINCE(6, 0)

        // TODO deprecate these after finding good replacements (use QPointingDevice::globalArea?)
        QPointF normalizedPos() const;
        QPointF startNormalizedPos() const;

        // TODO deprecate these after finding good replacements (store longer history perhaps?)
        QPointF lastPos() const;
        QPointF lastScenePos() const;
        QPointF lastScreenPos() const;
        QPointF lastNormalizedPos() const;

        QPointF position() const;
        QPointF pressPosition() const;
        QPointF scenePosition() const;
        QPointF scenePressPosition() const;
        QPointF globalPosition() const;
        QPointF globalPressPosition() const;

        qreal pressure() const;
        qreal rotation() const;
        QSizeF ellipseDiameters() const;

        QVector2D velocity() const;
        InfoFlags flags() const;
        QList<QPointF> rawScreenPositions() const;

        // internal
        // ### Qt 6: move private, rename appropriately, only friends can call them
#if QT_DEPRECATED_SINCE(6, 0)
        void setId(int id);
        void setUniqueId(qint64 uid);
        void setState(Qt::TouchPointStates state);
        void setPos(const QPointF &pos);
        void setScenePos(const QPointF &scenePos);
        void setScreenPos(const QPointF &screenPos);
        void setNormalizedPos(const QPointF &normalizedPos);
        void setStartPos(const QPointF &startPos);
        void setStartScenePos(const QPointF &startScenePos);
        void setStartScreenPos(const QPointF &startScreenPos);
        void setStartNormalizedPos(const QPointF &startNormalizedPos);
        void setLastPos(const QPointF &lastPos);
        void setLastScenePos(const QPointF &lastScenePos);
        void setLastScreenPos(const QPointF &lastScreenPos);
        void setLastNormalizedPos(const QPointF &lastNormalizedPos);
        void setPressure(qreal pressure);
        void setRotation(qreal angle);
        void setEllipseDiameters(const QSizeF &dia);
        void setVelocity(const QVector2D &v);
        void setFlags(InfoFlags flags);
        void setRawScreenPositions(const QList<QPointF> &positions);
#endif // QT_DEPRECATED_SINCE(6, 0)

    private:
        QTouchEventTouchPointPrivate *d;
        friend class QGuiApplication;
        friend class QGuiApplicationPrivate;
        friend class QApplication;
        friend class QApplicationPrivate;
        friend class QQuickPointerTouchEvent;
        friend class QQuickMultiPointTouchArea;
    };

    explicit QTouchEvent(QEvent::Type eventType,
                         const QPointingDevice *source = nullptr,
                         Qt::KeyboardModifiers modifiers = Qt::NoModifier,
                         Qt::TouchPointStates touchPointStates = Qt::TouchPointStates(),
                         const QList<QTouchEvent::TouchPoint> &touchPoints = QList<QTouchEvent::TouchPoint>());
    ~QTouchEvent();

    inline QWindow *window() const { return _window; }
    inline QObject *target() const { return _target; }
    inline Qt::TouchPointStates touchPointStates() const { return _touchPointStates; }
    inline const QList<QTouchEvent::TouchPoint> &touchPoints() const { return _touchPoints; }

    // ### Qt 6: move private, rename appropriately, only friends can call them; or just let friends modify variables directly
#if QT_DEPRECATED_SINCE(6, 0)
    inline void setWindow(QWindow *awindow) { _window = awindow; }
    inline void setTarget(QObject *atarget) { _target = atarget; }
    inline void setTouchPoints(const QList<QTouchEvent::TouchPoint> &atouchPoints) { _touchPoints = atouchPoints; }
#endif // QT_DEPRECATED_SINCE(6, 0)

protected:
    QWindow *_window;
    QObject *_target;
    Qt::TouchPointStates _touchPointStates;
    QList<QTouchEvent::TouchPoint> _touchPoints;

    friend class QGuiApplication;
    friend class QGuiApplicationPrivate;
    friend class QApplication;
    friend class QApplicationPrivate;
#ifndef QT_NO_GRAPHICSVIEW
    friend class QGraphicsScenePrivate; // direct access to _touchPoints
#endif
};
Q_DECLARE_TYPEINFO(QTouchEvent::TouchPoint, Q_MOVABLE_TYPE);
Q_DECLARE_OPERATORS_FOR_FLAGS(QTouchEvent::TouchPoint::InfoFlags)

#ifndef QT_NO_DEBUG_STREAM
Q_GUI_EXPORT QDebug operator<<(QDebug, const QTouchEvent::TouchPoint &);
#endif

class Q_GUI_EXPORT QScrollPrepareEvent : public QEvent
{
public:
    explicit QScrollPrepareEvent(const QPointF &startPos);
    ~QScrollPrepareEvent();

    QPointF startPos() const;

    QSizeF viewportSize() const;
    QRectF contentPosRange() const;
    QPointF contentPos() const;

    void setViewportSize(const QSizeF &size);
    void setContentPosRange(const QRectF &rect);
    void setContentPos(const QPointF &pos);

private:
    QPointF m_startPos;
    QSizeF m_viewportSize;
    QRectF m_contentPosRange;
    QPointF m_contentPos;
};


class Q_GUI_EXPORT QScrollEvent : public QEvent
{
public:
    enum ScrollState
    {
        ScrollStarted,
        ScrollUpdated,
        ScrollFinished
    };

    QScrollEvent(const QPointF &contentPos, const QPointF &overshoot, ScrollState scrollState);
    ~QScrollEvent();

    QPointF contentPos() const;
    QPointF overshootDistance() const;
    ScrollState scrollState() const;

private:
    QPointF m_contentPos;
    QPointF m_overshoot;
    QScrollEvent::ScrollState m_state;
};

class Q_GUI_EXPORT QScreenOrientationChangeEvent : public QEvent
{
public:
    QScreenOrientationChangeEvent(QScreen *screen, Qt::ScreenOrientation orientation);
    ~QScreenOrientationChangeEvent();

    QScreen *screen() const;
    Qt::ScreenOrientation orientation() const;

private:
    QScreen *m_screen;
    Qt::ScreenOrientation m_orientation;
};

class Q_GUI_EXPORT QApplicationStateChangeEvent : public QEvent
{
public:
    explicit QApplicationStateChangeEvent(Qt::ApplicationState state);
    Qt::ApplicationState applicationState() const;

private:
    Qt::ApplicationState m_applicationState;
};

QT_END_NAMESPACE

#endif // QEVENT_H
