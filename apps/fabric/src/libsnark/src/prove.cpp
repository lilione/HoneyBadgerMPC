#include <libsnark/common/default_types/r1cs_se_ppzksnark_pp.hpp>
#include <libsnark/zk_proof_systems/ppzksnark/r1cs_se_ppzksnark/r1cs_se_ppzksnark.hpp>
#include <libsnark/gadgetlib1/pb_variable.hpp>
#include <libsnark/gadgetlib1/gadgets/basic_gadgets.hpp>

#include "util.tcc"

using namespace libsnark;
using namespace std;

void printBuffer(const buffer_t* buf) {
    int32_t len = buf->length;
    for (int32_t i = 0; i < len; i++) {
        printf("%02X", buf->data[i]);
    }
}

int main (int argc, char *argv[]) {
    typedef libff::Fr<default_r1cs_se_ppzksnark_pp> FieldT;

    // Initialize the curve parameters
    default_r1cs_se_ppzksnark_pp::init_public_params();

    // Create protoboard
    protoboard<FieldT> pb;

    pb_variable<FieldT> x, max;
    pb_variable<FieldT> less, less_or_eq;

    x.allocate(pb, "x");
    max.allocate(pb, "max");

    pb.val(max)= atoi(argv[2]);

    comparison_gadget<FieldT> cmp(pb, 10, x, max, less, less_or_eq, "cmp");
    cmp.generate_r1cs_constraints();
    pb.add_r1cs_constraint(r1cs_constraint<FieldT>(less, 1, FieldT::one()));

    const r1cs_constraint_system<FieldT> constraint_system = pb.get_constraint_system();

    // generate keypair
    const r1cs_se_ppzksnark_keypair<default_r1cs_se_ppzksnark_pp> keypair = r1cs_se_ppzksnark_generator<default_r1cs_se_ppzksnark_pp>(constraint_system);

    // Add witness values
    pb.val(x) = atoi(argv[1]); // secret
    cmp.generate_r1cs_witness();

    // generate proof
    const r1cs_se_ppzksnark_proof<default_r1cs_se_ppzksnark_pp> proof = r1cs_se_ppzksnark_prover<default_r1cs_se_ppzksnark_pp>(keypair.pk, pb.primary_input(), pb.auxiliary_input());

    buffer_t vk_buf = createBuffer(keypair.vk);
    buffer_t proof_buf = createBuffer(proof);

    printf("result ");
    printBuffer(&vk_buf);
    printf(" ");
    printBuffer(&proof_buf);
    printf("\n");

 // verify
    bool verified = r1cs_se_ppzksnark_verifier_strong_IC<default_r1cs_se_ppzksnark_pp>(keypair.vk, pb.primary_input(), proof);

    cout << "Verification status: " << verified << endl;

    return 0;
}