from types import SimpleNamespace

from app import transcribe


async def test_start_registers_with_referral_once():
    from bot.handlers.start import register

    def msg(tg_id):
        return SimpleNamespace(from_user=SimpleNamespace(id=tg_id, username=None, first_name=f"U{tg_id}", last_name=None))

    inviter, _ = await register(msg(10), None)
    user, ref = await register(msg(11), inviter.ref_code)
    assert ref and ref.id == inviter.id and user.referrer_id == inviter.id
    again, ref2 = await register(msg(11), "ELS9999")  # второй /start не меняет реферала
    assert ref2 is None and again.referrer_id == inviter.id
    self_ref, ref3 = await register(msg(12), "ELS0003")  # свой же код (id=3) не засчитывается
    assert ref3 is None and self_ref.referrer_id is None


async def test_transcribe_disabled_without_key():
    assert transcribe.enabled() is False
