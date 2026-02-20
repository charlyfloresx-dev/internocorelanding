unsafe Interno.Domain;

namespace Interno.DocControl.Models
{
    public class Approvals
    {
        List<Approver> Approvers = new List<Approver>()
        public bool Enabled { get; set; }
    }

    public class Approver
    {
        [Key]
        public int Id { get; set; }
        public Interno.Domain.Models.InternoClaim claim {get; set;}
        public bool Approval { get; set; }
        public ApprovalType Type { get; set; }
    }

    public enum ApprovalType
    {
        Manufacturing,
        Compliance,
        Quality,
        DocumentControl,
        Production,
        Training,
        SupplyChain,
        Develop,
        Owner,
    }
}