from engine.his_parse import parse_his_csv, Subject
from engine.grade import grade_all, GradeConfig

# Subject entered at intake (Logan's inputs; GLA assumed 4,532 pending verification)
subject = Subject(
    address="Poipu Aina Pl (Ala Kinoiki), Koloa",
    tmk="4-2-8-22-31",
    gla=4532,
    lot_acres=2.47,
    tenure="Fee Simple",
    year_built=2022,
)

comps = parse_his_csv("/mnt/user-data/uploads/MLS_One_Line_07-17-2026_07_09_21AM.csv")
graded = grade_all(comps, subject, GradeConfig())

print(f"Subject: {subject.address}  ~{subject.gla:,.0f}sf  {subject.lot_acres}ac  {subject.tenure}\n")
print(f"Graded {len(graded)} candidates (leasehold gated). Top 15:\n")
for g in graded[:15]:
    c = g.comp
    price = f"${c.price:,.0f}" if c.price else "n/a"
    print(f"  [{g.score:6.1f}] {price:>12}  {c.location[:34]:<34} {c.zone:<9} {g.why()}")
