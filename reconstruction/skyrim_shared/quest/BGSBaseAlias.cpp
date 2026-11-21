// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// Code origin: community declarations; bodies written from the pinned listing
// 0x392c60 BGSBaseAlias::~BGSBaseAlias
#include "BGSBaseAlias.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BGSBaseAlias::BGSBaseAlias()
{
}

// TODO body: RVA 0x392c60, 66 bytes, BGSBaseAlias::~BGSBaseAlias; compared as the scalar deleting
// destructor. If the target calls a separate destructor, keep only the declaration and delete this
// definition (cookbook rule 18).
// ~BGSBaseAlias: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); releases the member block, then the object is freed by the deleting form.
BGSBaseAlias::~BGSBaseAlias()
{
    AliasMemberCleanupStub(&unknown08);
}
