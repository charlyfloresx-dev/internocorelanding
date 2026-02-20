using System.IO;

namespace Interno.DocControl.Models
{
    [Key]
    public int Id { get; set; }
    public string Name { get; set; }
    public string Description { get; set; }
    public List<Approver> Approvers { get; set; }
    public int Version { get; set; }
    public FileData Document { get; set; }
}