using System.ComponentModel.DataAnnotations;
namespace Interno.Domain.Catalog
{
    public class Reason
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        public string Name { get; set; }
        [RequiredAttribute]
        [MaxLengthAttribute(250)]
        public string Description { get; set; }
    }
}