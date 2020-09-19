from apps.fabric.src.client.Client import Client
from honeybadgermpc.polynomial import EvalPoint, polynomials_over
from honeybadgermpc.elliptic_curve import Subgroup
from honeybadgermpc.field import GF

field = GF(Subgroup.BLS12_381)

if __name__ == '__main__':
    client = Client.from_toml_config("apps/fabric/conf/config.toml")

    shares = [int('20712427879853309870484012063445495455271635217524728543703539671470719496959'),
              int('41424855759706619740968024126890990910543270435049457087407079342941438993918'),
              int('9701408464433739132004295682150520528124353152046547808506960314473577306364'),
              int('30413836344287049002488307745596015983395988369571276352210499985944296803323')]

    poly = polynomials_over(field)
    eval_point = EvalPoint(field, client.n, use_omega_powers=False)
    shares = [(eval_point(i), share) for i, share in enumerate(shares)]
    mask = poly.interpolate_at(shares, 0)

    print(mask)