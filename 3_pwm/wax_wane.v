// File: wax_wane.v
// Generated by MyHDL 0.11
// Date: Mon Nov 30 18:24:51 2020


`timescale 1ns/10ps

module wax_wane (
    clk_i,
    led_o
);


input clk_i;
output led_o;
wire led_o;

reg [22:0] rampout;
reg [3:0] k_cnt;
reg [22:0] chunk_insts_0_delta;



always @(posedge clk_i) begin: WAX_WANE_LOC_INSTS_CHUNK_INSTS_0_LOC_INSTS_CHUNK_INSTS_K
    rampout <= (rampout + chunk_insts_0_delta);
    if ((rampout == 1)) begin
        chunk_insts_0_delta <= 1;
    end
    else if (($signed({1'b0, rampout}) == (8388608 - 2))) begin
        chunk_insts_0_delta <= (-1);
    end
    else if ((chunk_insts_0_delta == 0)) begin
        chunk_insts_0_delta <= 1;
        rampout <= 1;
    end
end


always @(posedge clk_i) begin: WAX_WANE_LOC_INSTS_CHUNK_INSTS_K_LOC_INSTS_CHUNK_INSTS_0
    k_cnt <= (k_cnt + 1);
end



assign led_o = (k_cnt < rampout[23-1:19]);

endmodule
