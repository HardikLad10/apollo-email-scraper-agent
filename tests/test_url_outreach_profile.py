from pathlib import Path
import pytest

from outreach.profile import active_tex_text, load_candidate, select_profile, ProfileNeedsReview
from outreach.models import Context


def test_comments_do_not_become_claims():
    result = active_tex_text('% old 85%\n\\resumeItem{Reduced effort by 40\\%}')
    assert '85' not in result and '40%' in result


def test_selected_profile_has_no_other_big_stack(outreach_project):
    root = outreach_project
    context = Context('Example','example.org','Full Stack Engineer',None,'React APIs Docker',(),())
    candidate = load_candidate('fullstack', context, root=root, refresh=False)
    assert any('ChromaDB' in fact for fact in candidate.facts)
    assert not any('Drizzle' in fact for fact in candidate.facts)
    assert candidate.restrictions


def test_auto_selection_requires_override_for_overlap():
    context = Context('Example','example.org','AI Software Engineer',None,'',(),())
    with pytest.raises(ProfileNeedsReview):
        select_profile(context, 'auto')


def test_changed_source_holds_facts_and_readonly_preview(tmp_path):
    import hashlib,yaml
    sources={}
    for name in ('fullstack','amazon','accessibility'):
        source=tmp_path/(name+'.tex')
        source.write_text('\\begin{document}Reviewed fictional experience\\end{document}')
        sources[name]={'path':source.name,'reviewed_active_sha256':hashlib.sha256(active_tex_text(source.read_text()).encode()).hexdigest()}
    (tmp_path/'config').mkdir()
    (tmp_path/'config/outreach_profile_sources.yaml').write_text(yaml.safe_dump({'sources':sources}))
    profile=tmp_path/'profile.md'
    profile.write_text('Reviewed restrictions must remain.\n')
    changed=tmp_path/'fullstack.tex'
    changed.write_text('\\begin{document}Unreviewed new claim\\end{document}')
    context=Context('Example','example.org','Engineer',None,'',(),())
    with pytest.raises(ProfileNeedsReview): load_candidate('fullstack',context,root=tmp_path,refresh=False)
    assert profile.read_text()=='Reviewed restrictions must remain.\n'
    with pytest.raises(ProfileNeedsReview): load_candidate('fullstack',context,root=tmp_path,refresh=True)
    assert 'Unreviewed new claim' in profile.read_text()
    assert profile.read_text().startswith('Reviewed restrictions must remain.')
    assert changed.read_text()=='\\begin{document}Unreviewed new claim\\end{document}'
